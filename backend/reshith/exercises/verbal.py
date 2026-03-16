"""
Verbal sentence exercise generator for Biblical Hebrew.

Generates Hebrew-to-English exercises with verbs (participles) for lesson 4+.
Patterns include:
- Subject + Verb: "The X is verbing."
- Subject + Verb + Object: "The X is verbing the Y."
- Subject + Verb + Prep: "The X is verbing <prep> the Y."
- Subject + Verb + Object + Prep: "The X is verbing the Y <prep> the Z."
"""

import hashlib
import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

from reshith.core.config import get_settings
from reshith.exercises.article import Noun, add_definite_article, load_nouns_for_exercises
from reshith.exercises.sentences import (
    Preposition,
    attach_inseparable_preposition,
    load_prepositions,
)
from reshith.exercises.vocabulary import load_lessons_up_to

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "exercise_cache"


@dataclass
class Verb:
    hebrew: str
    transliteration: str
    definition: str
    lesson: int


@dataclass
class VerbalExercise:
    """A Hebrew-to-English verbal sentence exercise."""

    pattern: str
    hebrew: str
    transliteration: str
    english_answer: str
    components: dict[str, str]
    lesson: int = 1


@dataclass
class VerbalGradeResult:
    """Result of grading a verbal exercise."""

    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str


def load_verbs(max_lesson: int) -> list[Verb]:
    """Load verbs from vocabulary up to max_lesson."""
    vocab = load_lessons_up_to(max_lesson)
    return [
        Verb(
            hebrew=item.hebrew,
            transliteration=item.transliteration,
            definition=item.definition,
            lesson=item.lesson,
        )
        for item in vocab
        if item.category == "verbs"
    ]


def _get_verb_cache_key(
    verbs: list[Verb],
    nouns: list[Noun],
    preps: list[Preposition],
) -> str:
    """Generate a cache key for verb mappings."""
    verb_ids = sorted([v.transliteration for v in verbs])
    noun_ids = sorted([n.transliteration for n in nouns])
    prep_ids = sorted([p.transliteration for p in preps])
    content = json.dumps({"verbs": verb_ids, "nouns": noun_ids, "preps": prep_ids})
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_verb_cache_path(cache_key: str) -> Path:
    """Get the cache file path for verb mappings."""
    return CACHE_DIR / f"verb_map_{cache_key}.json"


async def generate_verb_mappings(
    verbs: list[Verb],
    nouns: list[Noun],
    preps: list[Preposition],
    force_refresh: bool = False,
) -> dict:
    """
    Generate mappings for verb-noun relationships using LLM.

    Returns:
        Dict with 'subjects', 'objects', 'prepositions' mappings
    """
    cache_key = _get_verb_cache_key(verbs, nouns, preps)
    cache_path = _get_verb_cache_path(cache_key)

    if not force_refresh and cache_path.exists():
        logger.debug(f"Loading verb mappings from cache: {cache_key}")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set, using fallback verb mappings")
        return _generate_fallback_verb_mappings(verbs, nouns, preps)

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    verb_list = [f"{v.transliteration} ({v.definition})" for v in verbs]
    noun_list = [f"{n.transliteration} ({n.definition})" for n in nouns]
    prep_list = [
        f"{p.transliteration} ({p.definition})"
        for p in preps
        if p.transliteration not in ("ʾēṯ", "ʾeṯ-")
    ]

    prompt = (
        "Given these Hebrew verbs (participles), nouns, and prepositions, determine:\n"
        "1. Which nouns can be SUBJECTS of each verb (who performs the action)\n"
        "2. Which nouns can be OBJECTS of each verb (what receives the action)\n"
        "3. Which prepositions each verb can take with which nouns\n\n"
        f"Verbs:\n{chr(10).join(f'- {v}' for v in verb_list)}\n\n"
        f"Nouns:\n{chr(10).join(f'- {n}' for n in noun_list)}\n\n"
        f"Prepositions:\n{chr(10).join(f'- {p}' for p in prep_list)}\n\n"
        "Guidelines:\n"
        "- Subjects: Animate nouns can typically be subjects\n"
        "- Objects: Consider semantic sense (eat food, write books, give things)\n"
        "- Prepositions: Consider typical usage (go TO places, sit ON thrones)\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "subjects": {"verb_translit": ["noun1", "noun2"]},\n'
        '  "objects": {"verb_translit": ["noun1", "noun2"]},\n'
        '  "prepositions": {"verb_translit": {"prep_translit": ["noun1", "noun2"]}}\n'
        "}\n\n"
        "Use exact transliterations provided. Be practical and realistic."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert in Biblical Hebrew helping to generate "
                        "sensible verb-noun relationships for language learning."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content or "{}")

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Generated and cached verb mappings: {cache_key}")
        return result

    except Exception as e:
        logger.error(f"Failed to generate verb mappings: {e}")
        return _generate_fallback_verb_mappings(verbs, nouns, preps)


def _generate_fallback_verb_mappings(
    verbs: list[Verb],
    nouns: list[Noun],
    preps: list[Preposition],
) -> dict:
    """Generate simple fallback verb mappings when LLM is unavailable."""
    animate_words = ["man", "woman", "boy", "king", "servant", "elder", "judge", "messenger"]
    location_words = ["house", "field", "city", "palace", "temple", "road", "river", "throne"]
    object_words = ["book", "word", "thing", "food", "bread"]

    animate_nouns = []
    location_nouns = []
    object_nouns = []

    for noun in nouns:
        defn = noun.definition.lower()
        if any(word in defn for word in animate_words):
            animate_nouns.append(noun.transliteration)
        if any(word in defn for word in location_words):
            location_nouns.append(noun.transliteration)
        if any(word in defn for word in object_words):
            object_nouns.append(noun.transliteration)

    subjects: dict[str, list[str]] = {}
    objects: dict[str, list[str]] = {}
    prepositions: dict[str, dict[str, list[str]]] = {}

    for verb in verbs:
        v_trans = verb.transliteration
        defn = verb.definition.lower()

        subjects[v_trans] = animate_nouns if animate_nouns else [n.transliteration for n in nouns]

        if "writing" in defn:
            objects[v_trans] = object_nouns if object_nouns else []
        elif "eating" in defn:
            objects[v_trans] = object_nouns if object_nouns else []
        elif "giving" in defn:
            objects[v_trans] = object_nouns + location_nouns
        else:
            objects[v_trans] = []

        prepositions[v_trans] = {}
        for prep in preps:
            if prep.transliteration in ("ʾēṯ", "ʾeṯ-"):
                continue

            p_defn = prep.definition.lower()
            if "to" in p_defn or "toward" in p_defn:
                prepositions[v_trans][prep.transliteration] = location_nouns + animate_nouns
            elif "in" in p_defn or "on" in p_defn:
                prepositions[v_trans][prep.transliteration] = location_nouns
            else:
                prepositions[v_trans][prep.transliteration] = [n.transliteration for n in nouns]

    return {
        "subjects": subjects,
        "objects": objects,
        "prepositions": prepositions,
    }


def _get_english_verb(verb: Verb) -> str:
    """Extract the primary English meaning from a verb definition."""
    return verb.definition.split(",")[0].strip().lower()


def _get_english_noun(noun: Noun) -> str:
    """Extract the primary English meaning from a noun definition."""
    return noun.definition.split(",")[0].strip().lower()


def _get_english_prep(prep: Preposition) -> str:
    """Extract the primary English meaning from a preposition definition."""
    return prep.definition.split(",")[0].strip().lower()


async def generate_subject_verb_exercise(
    verbs: list[Verb],
    nouns: list[Noun],
    verb_mappings: dict,
) -> VerbalExercise | None:
    """
    Generate "The X is verbing." pattern.
    """
    subjects_map = verb_mappings.get("subjects", {})

    valid_verbs = [
        v for v in verbs
        if v.transliteration in subjects_map and subjects_map[v.transliteration]
    ]
    if not valid_verbs:
        return None

    verb = random.choice(valid_verbs)
    subj_trans = random.choice(subjects_map[verb.transliteration])
    subj = next((n for n in nouns if n.transliteration == subj_trans), None)
    if not subj:
        return None

    subj_def_heb, subj_def_trans, _ = add_definite_article(subj)

    hebrew = f"{subj_def_heb} {verb.hebrew}."
    translit = f"{subj_def_trans} {verb.transliteration}."

    verb_eng = _get_english_verb(verb)
    subj_eng = _get_english_noun(subj)
    english = f"The {subj_eng} is {verb_eng}."

    return VerbalExercise(
        pattern="subject_verb",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "subject": subj.hebrew,
            "verb": verb.hebrew,
        },
        lesson=max(verb.lesson, subj.lesson),
    )


async def generate_subject_verb_object_exercise(
    verbs: list[Verb],
    nouns: list[Noun],
    verb_mappings: dict,
) -> VerbalExercise | None:
    """
    Generate "The X is verbing the Y." pattern with direct object marker.
    """
    subjects_map = verb_mappings.get("subjects", {})
    objects_map = verb_mappings.get("objects", {})

    valid_verbs = [
        v for v in verbs
        if v.transliteration in subjects_map
        and subjects_map[v.transliteration]
        and v.transliteration in objects_map
        and objects_map[v.transliteration]
    ]
    if not valid_verbs:
        return None

    verb = random.choice(valid_verbs)
    subj_trans = random.choice(subjects_map[verb.transliteration])
    obj_trans = random.choice(objects_map[verb.transliteration])

    subj = next((n for n in nouns if n.transliteration == subj_trans), None)
    obj = next((n for n in nouns if n.transliteration == obj_trans), None)
    if not subj or not obj:
        return None

    subj_def_heb, subj_def_trans, _ = add_definite_article(subj)
    obj_def_heb, obj_def_trans, _ = add_definite_article(obj)

    hebrew = f"{subj_def_heb} {verb.hebrew} אֶת־{obj_def_heb}."
    translit = f"{subj_def_trans} {verb.transliteration} ʾeṯ-{obj_def_trans}."

    verb_eng = _get_english_verb(verb)
    subj_eng = _get_english_noun(subj)
    obj_eng = _get_english_noun(obj)
    english = f"The {subj_eng} is {verb_eng} the {obj_eng}."

    return VerbalExercise(
        pattern="subject_verb_object",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "subject": subj.hebrew,
            "verb": verb.hebrew,
            "object": obj.hebrew,
        },
        lesson=max(verb.lesson, subj.lesson, obj.lesson),
    )


async def generate_subject_verb_prep_exercise(
    verbs: list[Verb],
    nouns: list[Noun],
    preps: list[Preposition],
    verb_mappings: dict,
) -> VerbalExercise | None:
    """
    Generate "The X is verbing <prep> the Y." pattern.
    """
    subjects_map = verb_mappings.get("subjects", {})
    prep_map = verb_mappings.get("prepositions", {})

    valid_verbs = [
        v for v in verbs
        if v.transliteration in subjects_map
        and subjects_map[v.transliteration]
        and v.transliteration in prep_map
        and prep_map[v.transliteration]
    ]
    if not valid_verbs:
        return None

    verb = random.choice(valid_verbs)
    subj_trans = random.choice(subjects_map[verb.transliteration])
    subj = next((n for n in nouns if n.transliteration == subj_trans), None)
    if not subj:
        return None

    verb_prep_map = prep_map[verb.transliteration]
    available_preps = [
        p for p in preps
        if p.transliteration in verb_prep_map and verb_prep_map[p.transliteration]
    ]
    if not available_preps:
        return None

    prep = random.choice(available_preps)
    prep_obj_trans = random.choice(verb_prep_map[prep.transliteration])
    prep_obj = next((n for n in nouns if n.transliteration == prep_obj_trans), None)
    if not prep_obj:
        return None

    subj_def_heb, subj_def_trans, _ = add_definite_article(subj)
    prep_obj_def_heb, prep_obj_def_trans, _ = add_definite_article(prep_obj)

    prep_phrase_heb, prep_phrase_trans = attach_inseparable_preposition(
        prep, prep_obj_def_heb, prep_obj_def_trans, has_article=True
    )

    hebrew = f"{subj_def_heb} {verb.hebrew} {prep_phrase_heb}."
    translit = f"{subj_def_trans} {verb.transliteration} {prep_phrase_trans}."

    verb_eng = _get_english_verb(verb)
    subj_eng = _get_english_noun(subj)
    prep_eng = _get_english_prep(prep)
    prep_obj_eng = _get_english_noun(prep_obj)
    english = f"The {subj_eng} is {verb_eng} {prep_eng} the {prep_obj_eng}."

    return VerbalExercise(
        pattern="subject_verb_prep",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "subject": subj.hebrew,
            "verb": verb.hebrew,
            "preposition": prep.hebrew,
            "prep_object": prep_obj.hebrew,
        },
        lesson=max(verb.lesson, subj.lesson, prep_obj.lesson),
    )


async def generate_subject_verb_object_prep_exercise(
    verbs: list[Verb],
    nouns: list[Noun],
    preps: list[Preposition],
    verb_mappings: dict,
) -> VerbalExercise | None:
    """
    Generate "The X is verbing the Y <prep> the Z." pattern.
    """
    subjects_map = verb_mappings.get("subjects", {})
    objects_map = verb_mappings.get("objects", {})
    prep_map = verb_mappings.get("prepositions", {})

    valid_verbs = [
        v for v in verbs
        if v.transliteration in subjects_map
        and subjects_map[v.transliteration]
        and v.transliteration in objects_map
        and objects_map[v.transliteration]
        and v.transliteration in prep_map
        and prep_map[v.transliteration]
    ]
    if not valid_verbs:
        return None

    verb = random.choice(valid_verbs)
    subj_trans = random.choice(subjects_map[verb.transliteration])
    obj_trans = random.choice(objects_map[verb.transliteration])

    subj = next((n for n in nouns if n.transliteration == subj_trans), None)
    obj = next((n for n in nouns if n.transliteration == obj_trans), None)
    if not subj or not obj:
        return None

    verb_prep_map = prep_map[verb.transliteration]
    available_preps = [
        p for p in preps
        if p.transliteration in verb_prep_map and verb_prep_map[p.transliteration]
    ]
    if not available_preps:
        return None

    prep = random.choice(available_preps)
    prep_obj_trans = random.choice(verb_prep_map[prep.transliteration])
    prep_obj = next((n for n in nouns if n.transliteration == prep_obj_trans), None)
    if not prep_obj:
        return None

    subj_def_heb, subj_def_trans, _ = add_definite_article(subj)
    obj_def_heb, obj_def_trans, _ = add_definite_article(obj)
    prep_obj_def_heb, prep_obj_def_trans, _ = add_definite_article(prep_obj)

    prep_phrase_heb, prep_phrase_trans = attach_inseparable_preposition(
        prep, prep_obj_def_heb, prep_obj_def_trans, has_article=True
    )

    hebrew = f"{subj_def_heb} {verb.hebrew} אֶת־{obj_def_heb} {prep_phrase_heb}."
    translit = f"{subj_def_trans} {verb.transliteration} ʾeṯ-{obj_def_trans} {prep_phrase_trans}."

    verb_eng = _get_english_verb(verb)
    subj_eng = _get_english_noun(subj)
    obj_eng = _get_english_noun(obj)
    prep_eng = _get_english_prep(prep)
    prep_obj_eng = _get_english_noun(prep_obj)
    english = f"The {subj_eng} is {verb_eng} the {obj_eng} {prep_eng} the {prep_obj_eng}."

    return VerbalExercise(
        pattern="subject_verb_object_prep",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "subject": subj.hebrew,
            "verb": verb.hebrew,
            "object": obj.hebrew,
            "preposition": prep.hebrew,
            "prep_object": prep_obj.hebrew,
        },
        lesson=max(verb.lesson, subj.lesson, obj.lesson, prep_obj.lesson),
    )


async def generate_verbal_exercises(
    max_lesson: int = 4,
    count: int = 10,
    patterns: list[str] | None = None,
    pattern_weights: dict[str, float] | None = None,
) -> list[VerbalExercise]:
    """
    Generate Hebrew-to-English verbal sentence exercises.

    Args:
        max_lesson: Include vocabulary up to this lesson (must be >= 4 for verbs)
        count: Number of exercises to generate
        patterns: Filter to specific patterns. Options:
            - "subject_verb": "The X is verbing."
            - "subject_verb_object": "The X is verbing the Y."
            - "subject_verb_prep": "The X is verbing <prep> the Y."
            - "subject_verb_object_prep": "The X is verbing the Y <prep> the Z."
        pattern_weights: Optional weights for pattern selection

    Returns:
        List of VerbalExercise objects
    """
    if patterns is None:
        patterns = [
            "subject_verb",
            "subject_verb_object",
            "subject_verb_prep",
            "subject_verb_object_prep",
        ]

    if pattern_weights is None:
        pattern_weights = {
            "subject_verb": 0.25,
            "subject_verb_object": 0.30,
            "subject_verb_prep": 0.25,
            "subject_verb_object_prep": 0.20,
        }

    verbs = load_verbs(max_lesson)
    nouns = load_nouns_for_exercises(max_lesson)
    preps = load_prepositions(max_lesson)

    if not verbs or not nouns:
        return []

    verb_mappings = await generate_verb_mappings(verbs, nouns, preps)

    exercises: list[VerbalExercise] = []
    attempts = 0
    max_attempts = count * 3

    available_patterns = [p for p in patterns if p in pattern_weights]
    weights = [pattern_weights.get(p, 1.0) for p in available_patterns]

    while len(exercises) < count and attempts < max_attempts:
        attempts += 1
        pattern = random.choices(available_patterns, weights=weights)[0]

        exercise = None
        if pattern == "subject_verb":
            exercise = await generate_subject_verb_exercise(verbs, nouns, verb_mappings)
        elif pattern == "subject_verb_object":
            exercise = await generate_subject_verb_object_exercise(verbs, nouns, verb_mappings)
        elif pattern == "subject_verb_prep":
            exercise = await generate_subject_verb_prep_exercise(verbs, nouns, preps, verb_mappings)
        elif pattern == "subject_verb_object_prep":
            exercise = await generate_subject_verb_object_prep_exercise(
                verbs, nouns, preps, verb_mappings
            )

        if exercise:
            exercises.append(exercise)

    return exercises


def normalize_english_for_grading(text: str) -> str:
    """Normalize English text for comparison during grading."""
    normalized = text.strip().lower()
    normalized = normalized.replace("  ", " ")
    normalized = normalized.rstrip(".?!")
    return normalized


def grade_verbal_exercise(
    submitted: str,
    expected_english: str,
) -> VerbalGradeResult:
    """
    Grade a Hebrew-to-English verbal translation.

    Args:
        submitted: Student's English answer
        expected_english: Correct English answer

    Returns:
        VerbalGradeResult with score and feedback
    """
    submitted_norm = normalize_english_for_grading(submitted)
    expected_norm = normalize_english_for_grading(expected_english)

    if submitted_norm == expected_norm:
        return VerbalGradeResult(
            correct=True,
            score=1.0,
            expected=expected_english,
            submitted=submitted,
            feedback="Correct!",
        )

    submitted_words = submitted_norm.split()
    expected_words = expected_norm.split()

    if len(submitted_words) == len(expected_words):
        matches = sum(
            1 for s, e in zip(submitted_words, expected_words)
            if s == e or (s in ("is", "are") and e in ("is", "are"))
        )

        if matches == len(expected_words):
            return VerbalGradeResult(
                correct=True,
                score=1.0,
                expected=expected_english,
                submitted=submitted,
                feedback="Correct! (Minor variation accepted)",
            )

        if matches >= len(expected_words) - 1:
            return VerbalGradeResult(
                correct=False,
                score=0.8,
                expected=expected_english,
                submitted=submitted,
                feedback=f"Almost correct. Expected: {expected_english}",
            )

    score = 0.0
    verb_words = ["writing", "eating", "giving", "going", "sitting", "walking", "dwelling"]
    if any(word in submitted_norm for word in verb_words):
        score += 0.3

    if any(word in submitted_norm for word in expected_words[:3]):
        score += 0.3

    return VerbalGradeResult(
        correct=False,
        score=min(score, 0.7),
        expected=expected_english,
        submitted=submitted,
        feedback=f"Incorrect. Expected: {expected_english}",
    )
