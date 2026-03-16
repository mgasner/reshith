"""
Sentence-level exercise generator for Biblical Hebrew.

Generates exercises like:
- "Where is X? X is <prep> Y."
- "X is <prep> Y."
- "X and Y are <prep> Z."

Uses LLM to determine sensible noun-preposition-noun relationships.
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
from reshith.exercises.vocabulary import load_lessons_up_to

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "exercise_cache"


@dataclass
class Preposition:
    hebrew: str
    transliteration: str
    definition: str
    is_inseparable: bool


@dataclass
class Adverb:
    hebrew: str
    transliteration: str
    definition: str


@dataclass
class Conjunction:
    hebrew: str
    transliteration: str
    definition: str


def load_prepositions(max_lesson: int) -> list[Preposition]:
    """Load prepositions from vocabulary up to max_lesson."""
    vocab = load_lessons_up_to(max_lesson)
    preps = []
    for item in vocab:
        if item.category == "prepositions":
            is_inseparable = item.hebrew in ("בְּ", "לְ", "כְּ")
            preps.append(
                Preposition(
                    hebrew=item.hebrew,
                    transliteration=item.transliteration,
                    definition=item.definition,
                    is_inseparable=is_inseparable,
                )
            )
    return preps


def load_adverbs(max_lesson: int) -> list[Adverb]:
    """Load adverbs from vocabulary up to max_lesson."""
    vocab = load_lessons_up_to(max_lesson)
    return [
        Adverb(
            hebrew=item.hebrew,
            transliteration=item.transliteration,
            definition=item.definition,
        )
        for item in vocab
        if item.category == "adverbs"
    ]


def load_conjunctions(max_lesson: int) -> list[Conjunction]:
    """Load conjunctions from vocabulary up to max_lesson."""
    vocab = load_lessons_up_to(max_lesson)
    return [
        Conjunction(
            hebrew=item.hebrew,
            transliteration=item.transliteration,
            definition=item.definition,
        )
        for item in vocab
        if item.category == "conjunction"
    ]


def _get_cache_key(nouns: list[Noun], preps: list[Preposition]) -> str:
    """Generate a cache key for noun-prep mapping."""
    noun_ids = sorted([n.transliteration for n in nouns])
    prep_ids = sorted([p.transliteration for p in preps])
    content = json.dumps({"nouns": noun_ids, "preps": prep_ids})
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_cache_path(cache_key: str) -> Path:
    """Get the cache file path for a given key."""
    return CACHE_DIR / f"noun_prep_map_{cache_key}.json"


async def generate_noun_prep_mapping(
    nouns: list[Noun],
    preps: list[Preposition],
    force_refresh: bool = False,
) -> dict[str, dict[str, list[str]]]:
    """
    Generate mapping of which nouns can sensibly relate to other nouns via prepositions.
    Uses LLM to determine sensible relationships, with caching.

    Returns:
        Dict mapping noun transliterations to {preposition: [compatible_nouns]}
    """
    cache_key = _get_cache_key(nouns, preps)
    cache_path = _get_cache_path(cache_key)

    if not force_refresh and cache_path.exists():
        logger.debug(f"Loading noun-prep mapping from cache: {cache_key}")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set, using fallback noun-prep mapping")
        return _generate_fallback_mapping(nouns, preps)

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    noun_list = [f"{n.transliteration} ({n.definition})" for n in nouns]
    prep_list = [f"{p.transliteration} ({p.definition})" for p in preps]

    prompt = (
        "Given these Biblical Hebrew nouns and prepositions, "
        "determine which nouns can sensibly relate to other nouns via each preposition.\n\n"
        f"Nouns:\n{chr(10).join(f'- {n}' for n in noun_list)}\n\n"
        f"Prepositions:\n{chr(10).join(f'- {p}' for p in prep_list)}\n\n"
        "For each noun, list which other nouns it can sensibly relate to via each "
        "preposition. Consider physical and logical relationships. For example:\n"
        '- A "boy" can be "in" (bə) a "house", "on" (ʿal) a "road"\n'
        '- A "house" can be "on" (ʿal) a "road", "near" (ʾēṣel) a "river"\n'
        '- A "king" can be "in" (bə) a "palace", "near" (ʾēṣel) a "city"\n\n'
        "Return ONLY a JSON object with this structure:\n"
        "{\n"
        '  "noun_transliteration": {\n'
        '    "preposition_transliteration": ["compatible_noun1", "compatible_noun2"]\n'
        "  }\n"
        "}\n\n"
        "Use the exact transliterations provided. Be practical and realistic.\n"
        "Only include relationships that would make sense in simple Biblical Hebrew sentences."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert in Biblical Hebrew helping to generate "
                        "sensible noun-preposition relationships for language learning."
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

        logger.info(f"Generated and cached noun-prep mapping: {cache_key}")
        return result

    except Exception as e:
        logger.error(f"Failed to generate noun-prep mapping: {e}")
        return _generate_fallback_mapping(nouns, preps)


def _generate_fallback_mapping(
    nouns: list[Noun],
    preps: list[Preposition],
) -> dict[str, dict[str, list[str]]]:
    """Generate a simple fallback mapping when LLM is unavailable."""
    result: dict[str, dict[str, list[str]]] = {}

    location_nouns = []
    animate_nouns = []
    other_nouns = []

    location_words = [
        "house", "field", "city", "palace", "temple",
        "road", "river", "land", "mountain", "garden",
    ]
    animate_words = ["man", "woman", "boy", "king", "servant", "elder", "child"]

    for noun in nouns:
        defn = noun.definition.lower()
        if any(word in defn for word in location_words):
            location_nouns.append(noun.transliteration)
        elif any(word in defn for word in animate_words):
            animate_nouns.append(noun.transliteration)
        else:
            other_nouns.append(noun.transliteration)

    for noun in nouns:
        result[noun.transliteration] = {}
        for prep in preps:
            if prep.transliteration in ("bə", "lə", "kə"):
                if noun.transliteration in animate_nouns:
                    result[noun.transliteration][prep.transliteration] = location_nouns
                else:
                    result[noun.transliteration][prep.transliteration] = [
                        n for n in location_nouns if n != noun.transliteration
                    ]
            elif "near" in prep.definition.lower() or "beside" in prep.definition.lower():
                all_others = [
                    n.transliteration for n in nouns
                    if n.transliteration != noun.transliteration
                ]
                result[noun.transliteration][prep.transliteration] = all_others
            elif "on" in prep.definition.lower() or "upon" in prep.definition.lower():
                result[noun.transliteration][prep.transliteration] = location_nouns

    return result


def attach_inseparable_preposition(
    prep: Preposition,
    noun_hebrew: str,
    noun_trans: str,
    has_article: bool = False,
) -> tuple[str, str]:
    """
    Attach an inseparable preposition to a noun.

    Handles the phonological rules for בְּ, לְ, כְּ before the definite article.
    """
    if not prep.is_inseparable:
        if has_article:
            return f"{prep.hebrew}־{noun_hebrew}", f"{prep.transliteration}-{noun_trans}"
        return f"{prep.hebrew} {noun_hebrew}", f"{prep.transliteration} {noun_trans}"

    base_letter = prep.hebrew[0]

    if has_article:
        if noun_hebrew.startswith("הַ"):
            noun_without_he = noun_hebrew[2:]
            dagesh = "\u05BC"
            if base_letter in "בגדכפת":
                result_heb = base_letter + "ַ" + dagesh + noun_without_he
            else:
                result_heb = base_letter + "ַ" + noun_without_he
            result_trans = prep.transliteration[0] + "a" + noun_trans[2:]
            return result_heb, result_trans
        elif noun_hebrew.startswith("הָ"):
            noun_without_he = noun_hebrew[2:]
            result_heb = base_letter + "ָ" + noun_without_he
            result_trans = prep.transliteration[0] + "ā" + noun_trans[2:]
            return result_heb, result_trans
        elif noun_hebrew.startswith("הֶ"):
            noun_without_he = noun_hebrew[2:]
            result_heb = base_letter + "ֶ" + noun_without_he
            result_trans = prep.transliteration[0] + "e" + noun_trans[2:]
            return result_heb, result_trans

    return prep.hebrew + noun_hebrew, prep.transliteration + noun_trans


@dataclass
class SentenceExercise:
    pattern: str
    hebrew: str
    transliteration: str
    english: str
    components: dict[str, str]
    lesson: int = 1


async def generate_where_is_x_exercise(
    nouns: list[Noun],
    preps: list[Preposition],
    adverbs: list[Adverb],
    noun_prep_map: dict[str, dict[str, list[str]]],
) -> SentenceExercise | None:
    """
    Generate "Where is X? X is <prep> Y." pattern.
    """
    where_adv = None
    for adv in adverbs:
        if "where" in adv.definition.lower():
            where_adv = adv
            break

    if not where_adv:
        return None

    valid_nouns = [
        n for n in nouns
        if n.transliteration in noun_prep_map and noun_prep_map[n.transliteration]
    ]
    if not valid_nouns:
        return None

    noun1 = random.choice(valid_nouns)
    noun1_map = noun_prep_map.get(noun1.transliteration, {})
    available_preps = [p for p in preps if p.transliteration in noun1_map]
    if not available_preps:
        return None

    prep = random.choice(available_preps)
    compatible_nouns = noun1_map.get(prep.transliteration, [])
    if not compatible_nouns:
        return None

    noun2_trans = random.choice(compatible_nouns)
    noun2 = next((n for n in nouns if n.transliteration == noun2_trans), None)
    if not noun2:
        return None

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
    noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)

    prep_phrase_heb, prep_phrase_trans = attach_inseparable_preposition(
        prep, noun2_def_heb, noun2_def_trans, has_article=True
    )

    question_heb = f"{where_adv.hebrew} {noun1_def_heb}"
    answer_heb = f"{noun1_def_heb} {prep_phrase_heb}"

    question_trans = f"{where_adv.transliteration} {noun1_def_trans}"
    answer_trans = f"{noun1_def_trans} {prep_phrase_trans}"

    noun1_eng = noun1.definition.split(",")[0].strip().lower()
    noun2_eng = noun2.definition.split(",")[0].strip().lower()
    prep_eng = prep.definition.split(",")[0].strip().lower()

    english = f"Where is the {noun1_eng}? The {noun1_eng} is {prep_eng} the {noun2_eng}."

    return SentenceExercise(
        pattern="where_is_x",
        hebrew=f"{question_heb}? {answer_heb}.",
        transliteration=f"{question_trans}? {answer_trans}.",
        english=english,
        components={
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "preposition": prep.hebrew,
            "adverb": where_adv.hebrew,
        },
        lesson=max(noun1.lesson, noun2.lesson),
    )


async def generate_x_is_prep_y_exercise(
    nouns: list[Noun],
    preps: list[Preposition],
    noun_prep_map: dict[str, dict[str, list[str]]],
) -> SentenceExercise | None:
    """Generate "X is <prep> Y." pattern."""
    valid_nouns = [
        n for n in nouns
        if n.transliteration in noun_prep_map and noun_prep_map[n.transliteration]
    ]
    if not valid_nouns:
        return None

    noun1 = random.choice(valid_nouns)
    noun1_map = noun_prep_map.get(noun1.transliteration, {})
    available_preps = [p for p in preps if p.transliteration in noun1_map]
    if not available_preps:
        return None

    prep = random.choice(available_preps)
    compatible_nouns = noun1_map.get(prep.transliteration, [])
    if not compatible_nouns:
        return None

    noun2_trans = random.choice(compatible_nouns)
    noun2 = next((n for n in nouns if n.transliteration == noun2_trans), None)
    if not noun2:
        return None

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
    noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)

    prep_phrase_heb, prep_phrase_trans = attach_inseparable_preposition(
        prep, noun2_def_heb, noun2_def_trans, has_article=True
    )

    hebrew = f"{noun1_def_heb} {prep_phrase_heb}"
    transliteration = f"{noun1_def_trans} {prep_phrase_trans}"

    noun1_eng = noun1.definition.split(",")[0].strip().lower()
    noun2_eng = noun2.definition.split(",")[0].strip().lower()
    prep_eng = prep.definition.split(",")[0].strip().lower()

    english = f"The {noun1_eng} is {prep_eng} the {noun2_eng}."

    return SentenceExercise(
        pattern="x_is_prep_y",
        hebrew=f"{hebrew}.",
        transliteration=f"{transliteration}.",
        english=english,
        components={
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "preposition": prep.hebrew,
        },
        lesson=max(noun1.lesson, noun2.lesson),
    )


async def generate_x_and_y_are_prep_z_exercise(
    nouns: list[Noun],
    preps: list[Preposition],
    conjunctions: list[Conjunction],
    noun_prep_map: dict[str, dict[str, list[str]]],
) -> SentenceExercise | None:
    """Generate "X and Y are <prep> Z." pattern."""
    and_conj = None
    for conj in conjunctions:
        if "and" in conj.definition.lower():
            and_conj = conj
            break

    if not and_conj:
        return None

    valid_nouns = [
        n for n in nouns
        if n.transliteration in noun_prep_map and noun_prep_map[n.transliteration]
    ]
    if len(valid_nouns) < 3:
        return None

    noun1, noun2 = random.sample(valid_nouns, 2)

    shared_preps = set(noun_prep_map.get(noun1.transliteration, {}).keys()) & set(
        noun_prep_map.get(noun2.transliteration, {}).keys()
    )
    available_preps = [p for p in preps if p.transliteration in shared_preps]
    if not available_preps:
        return None

    prep = random.choice(available_preps)

    compatible1 = set(noun_prep_map[noun1.transliteration].get(prep.transliteration, []))
    compatible2 = set(noun_prep_map[noun2.transliteration].get(prep.transliteration, []))
    shared_compatible = compatible1 & compatible2

    shared_compatible.discard(noun1.transliteration)
    shared_compatible.discard(noun2.transliteration)

    if not shared_compatible:
        return None

    noun3_trans = random.choice(list(shared_compatible))
    noun3 = next((n for n in nouns if n.transliteration == noun3_trans), None)
    if not noun3:
        return None

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
    noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)
    noun3_def_heb, noun3_def_trans, _ = add_definite_article(noun3)

    noun2_with_conj_heb = and_conj.hebrew + noun2_def_heb
    noun2_with_conj_trans = and_conj.transliteration + noun2_def_trans

    prep_phrase_heb, prep_phrase_trans = attach_inseparable_preposition(
        prep, noun3_def_heb, noun3_def_trans, has_article=True
    )

    hebrew = f"{noun1_def_heb} {noun2_with_conj_heb} {prep_phrase_heb}"
    transliteration = f"{noun1_def_trans} {noun2_with_conj_trans} {prep_phrase_trans}"

    noun1_eng = noun1.definition.split(",")[0].strip().lower()
    noun2_eng = noun2.definition.split(",")[0].strip().lower()
    noun3_eng = noun3.definition.split(",")[0].strip().lower()
    prep_eng = prep.definition.split(",")[0].strip().lower()

    english = f"The {noun1_eng} and the {noun2_eng} are {prep_eng} the {noun3_eng}."

    return SentenceExercise(
        pattern="x_and_y_are_prep_z",
        hebrew=f"{hebrew}.",
        transliteration=f"{transliteration}.",
        english=english,
        components={
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "noun3": noun3.hebrew,
            "preposition": prep.hebrew,
            "conjunction": and_conj.hebrew,
        },
        lesson=max(noun1.lesson, noun2.lesson, noun3.lesson),
    )


async def generate_sentence_exercises(
    max_lesson: int = 1,
    count: int = 10,
    patterns: list[str] | None = None,
) -> list[SentenceExercise]:
    """
    Generate sentence-level exercises.

    Args:
        max_lesson: Include vocabulary up to this lesson
        count: Number of exercises to generate
        patterns: Filter to specific patterns (where_is_x, x_is_prep_y, x_and_y_are_prep_z)

    Returns:
        List of SentenceExercise objects
    """
    if patterns is None:
        patterns = ["where_is_x", "x_is_prep_y", "x_and_y_are_prep_z"]

    nouns = load_nouns_for_exercises(max_lesson)
    preps = load_prepositions(max_lesson)
    adverbs = load_adverbs(max_lesson)
    conjunctions = load_conjunctions(max_lesson)

    if not nouns or not preps:
        return []

    noun_prep_map = await generate_noun_prep_mapping(nouns, preps)

    exercises = []
    attempts = 0
    max_attempts = count * 3

    while len(exercises) < count and attempts < max_attempts:
        attempts += 1
        pattern = random.choice(patterns)

        exercise = None
        if pattern == "where_is_x":
            exercise = await generate_where_is_x_exercise(nouns, preps, adverbs, noun_prep_map)
        elif pattern == "x_is_prep_y":
            exercise = await generate_x_is_prep_y_exercise(nouns, preps, noun_prep_map)
        elif pattern == "x_and_y_are_prep_z":
            exercise = await generate_x_and_y_are_prep_z_exercise(
                nouns, preps, conjunctions, noun_prep_map
            )

        if exercise:
            exercises.append(exercise)

    return exercises
