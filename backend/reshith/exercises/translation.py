"""
English-to-Hebrew translation exercise generator for Biblical Hebrew.

Generates exercises where students translate English sentences to Hebrew,
following Lambdin's textbook patterns.
"""

import random
import unicodedata
from dataclasses import dataclass

from reshith.exercises.article import Noun, add_definite_article, load_nouns_for_exercises
from reshith.exercises.sentences import (
    Adverb,
    Conjunction,
    Preposition,
    attach_inseparable_preposition,
    generate_noun_prep_mapping,
    load_adverbs,
    load_conjunctions,
    load_prepositions,
)


@dataclass
class TranslationExercise:
    """An English-to-Hebrew translation exercise."""

    pattern: str
    english: str
    hebrew_answer: str
    transliteration_answer: str
    components: dict[str, str]
    lesson: int = 1


@dataclass
class TranslationGradeResult:
    """Result of grading a translation exercise."""

    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str
    transliteration: str


def _get_english_noun(noun: Noun) -> str:
    """Extract the primary English meaning from a noun definition."""
    return noun.definition.split(",")[0].strip().lower()


def _get_english_prep(prep: Preposition) -> str:
    """Extract the primary English meaning from a preposition definition."""
    return prep.definition.split(",")[0].strip().lower()


async def generate_where_question_exercise(
    nouns: list[Noun],
    adverbs: list[Adverb],
    conjunctions: list[Conjunction],
    use_plural: bool | None = None,
) -> TranslationExercise | None:
    """
    Generate "Where is/are X (and Y)?" exercise.

    Args:
        nouns: Available nouns
        adverbs: Available adverbs (must include "where")
        conjunctions: Available conjunctions (for plural form)
        use_plural: If True, use "X and Y" form. If None, random.

    Returns:
        TranslationExercise or None if cannot generate
    """
    where_adv = next((a for a in adverbs if "where" in a.definition.lower()), None)
    if not where_adv:
        return None

    if use_plural is None:
        use_plural = random.choice([True, False])

    if use_plural:
        and_conj = next((c for c in conjunctions if "and" in c.definition.lower()), None)
        if not and_conj or len(nouns) < 2:
            use_plural = False

    if use_plural:
        noun1, noun2 = random.sample(nouns, 2)

        noun1_eng = _get_english_noun(noun1)
        noun2_eng = _get_english_noun(noun2)
        english = f"Where are the {noun1_eng} and the {noun2_eng}?"

        noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
        noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)

        and_conj = next(c for c in conjunctions if "and" in c.definition.lower())
        conj_noun2_heb = and_conj.hebrew + noun2_def_heb
        conj_noun2_trans = and_conj.transliteration + noun2_def_trans

        hebrew = f"{where_adv.hebrew} {noun1_def_heb} {conj_noun2_heb}?"
        translit = f"{where_adv.transliteration} {noun1_def_trans} {conj_noun2_trans}?"

        components = {
            "adverb": where_adv.hebrew,
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "conjunction": and_conj.hebrew,
        }
        lesson = max(noun1.lesson, noun2.lesson)
    else:
        noun = random.choice(nouns)
        noun_eng = _get_english_noun(noun)
        english = f"Where is the {noun_eng}?"

        noun_def_heb, noun_def_trans, _ = add_definite_article(noun)

        hebrew = f"{where_adv.hebrew} {noun_def_heb}?"
        translit = f"{where_adv.transliteration} {noun_def_trans}?"

        components = {
            "adverb": where_adv.hebrew,
            "noun1": noun.hebrew,
        }
        lesson = noun.lesson

    return TranslationExercise(
        pattern="where_question",
        english=english,
        hebrew_answer=hebrew,
        transliteration_answer=translit,
        components=components,
        lesson=lesson,
    )


async def generate_simple_statement_exercise(
    nouns: list[Noun],
    preps: list[Preposition],
    noun_prep_map: dict[str, dict[str, list[str]]],
) -> TranslationExercise | None:
    """
    Generate "The X is <prep> the Y." exercise.

    Args:
        nouns: Available nouns
        preps: Available prepositions
        noun_prep_map: Mapping of noun-preposition relationships

    Returns:
        TranslationExercise or None if cannot generate
    """
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

    noun1_eng = _get_english_noun(noun1)
    noun2_eng = _get_english_noun(noun2)
    prep_eng = _get_english_prep(prep)
    english = f"The {noun1_eng} is {prep_eng} the {noun2_eng}."

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
    noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)

    prep_noun_heb, prep_noun_trans = attach_inseparable_preposition(
        prep, noun2_def_heb, noun2_def_trans, has_article=True
    )

    hebrew = f"{noun1_def_heb} {prep_noun_heb}."
    translit = f"{noun1_def_trans} {prep_noun_trans}."

    return TranslationExercise(
        pattern="simple_statement",
        english=english,
        hebrew_answer=hebrew,
        transliteration_answer=translit,
        components={
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "preposition": prep.hebrew,
        },
        lesson=max(noun1.lesson, noun2.lesson),
    )


async def generate_conjunction_exercise(
    nouns: list[Noun],
    preps: list[Preposition],
    conjunctions: list[Conjunction],
    noun_prep_map: dict[str, dict[str, list[str]]],
) -> TranslationExercise | None:
    """
    Generate "The X and the Y are <prep> the Z." exercise.

    Args:
        nouns: Available nouns
        preps: Available prepositions
        conjunctions: Available conjunctions
        noun_prep_map: Mapping of noun-preposition relationships

    Returns:
        TranslationExercise or None if cannot generate
    """
    and_conj = next((c for c in conjunctions if "and" in c.definition.lower()), None)
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

    noun1_eng = _get_english_noun(noun1)
    noun2_eng = _get_english_noun(noun2)
    noun3_eng = _get_english_noun(noun3)
    prep_eng = _get_english_prep(prep)
    english = f"The {noun1_eng} and the {noun2_eng} are {prep_eng} the {noun3_eng}."

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)
    noun2_def_heb, noun2_def_trans, _ = add_definite_article(noun2)
    noun3_def_heb, noun3_def_trans, _ = add_definite_article(noun3)

    conj_noun2_heb = and_conj.hebrew + noun2_def_heb
    conj_noun2_trans = and_conj.transliteration + noun2_def_trans

    prep_loc_heb, prep_loc_trans = attach_inseparable_preposition(
        prep, noun3_def_heb, noun3_def_trans, has_article=True
    )

    hebrew = f"{noun1_def_heb} {conj_noun2_heb} {prep_loc_heb}."
    translit = f"{noun1_def_trans} {conj_noun2_trans} {prep_loc_trans}."

    return TranslationExercise(
        pattern="conjunction",
        english=english,
        hebrew_answer=hebrew,
        transliteration_answer=translit,
        components={
            "noun1": noun1.hebrew,
            "noun2": noun2.hebrew,
            "noun3": noun3.hebrew,
            "preposition": prep.hebrew,
            "conjunction": and_conj.hebrew,
        },
        lesson=max(noun1.lesson, noun2.lesson, noun3.lesson),
    )


async def generate_translation_exercises(
    max_lesson: int = 1,
    count: int = 10,
    patterns: list[str] | None = None,
    pattern_weights: dict[str, float] | None = None,
) -> list[TranslationExercise]:
    """
    Generate English-to-Hebrew translation exercises.

    Args:
        max_lesson: Include vocabulary up to this lesson
        count: Number of exercises to generate
        patterns: Filter to specific patterns. Options:
            - "where_question": "Where is/are X (and Y)?"
            - "simple_statement": "The X is <prep> the Y."
            - "conjunction": "The X and the Y are <prep> the Z."
        pattern_weights: Optional weights for pattern selection

    Returns:
        List of TranslationExercise objects
    """
    if patterns is None:
        patterns = ["where_question", "simple_statement", "conjunction"]

    if pattern_weights is None:
        pattern_weights = {
            "where_question": 0.25,
            "simple_statement": 0.50,
            "conjunction": 0.25,
        }

    nouns = load_nouns_for_exercises(max_lesson)
    preps = load_prepositions(max_lesson)
    adverbs = load_adverbs(max_lesson)
    conjunctions = load_conjunctions(max_lesson)

    if not nouns:
        return []

    noun_prep_map = await generate_noun_prep_mapping(nouns, preps)

    exercises: list[TranslationExercise] = []
    attempts = 0
    max_attempts = count * 3

    available_patterns = [p for p in patterns if p in pattern_weights]
    weights = [pattern_weights.get(p, 1.0) for p in available_patterns]

    while len(exercises) < count and attempts < max_attempts:
        attempts += 1
        pattern = random.choices(available_patterns, weights=weights)[0]

        exercise = None
        if pattern == "where_question":
            exercise = await generate_where_question_exercise(
                nouns, adverbs, conjunctions
            )
        elif pattern == "simple_statement":
            exercise = await generate_simple_statement_exercise(
                nouns, preps, noun_prep_map
            )
        elif pattern == "conjunction":
            exercise = await generate_conjunction_exercise(
                nouns, preps, conjunctions, noun_prep_map
            )

        if exercise:
            exercises.append(exercise)

    return exercises


def normalize_hebrew_for_grading(text: str) -> str:
    """Normalize Hebrew text for comparison during grading."""
    text = unicodedata.normalize("NFC", text)
    result = []
    for char in text:
        code = ord(char)
        if 0x0591 <= code <= 0x05AF:
            continue
        result.append(char)
    normalized = "".join(result).strip()
    normalized = normalized.replace("  ", " ")
    normalized = normalized.rstrip(".?!")
    return normalized


def grade_translation(
    submitted: str,
    expected_hebrew: str,
    expected_transliteration: str,
) -> TranslationGradeResult:
    """
    Grade an English-to-Hebrew translation.

    Args:
        submitted: Student's Hebrew answer
        expected_hebrew: Correct Hebrew answer
        expected_transliteration: Correct transliteration (for feedback)

    Returns:
        TranslationGradeResult with score and feedback
    """
    submitted_norm = normalize_hebrew_for_grading(submitted)
    expected_norm = normalize_hebrew_for_grading(expected_hebrew)

    if submitted_norm == expected_norm:
        return TranslationGradeResult(
            correct=True,
            score=1.0,
            expected=expected_hebrew,
            submitted=submitted,
            feedback="Correct!",
            transliteration=expected_transliteration,
        )

    submitted_words = submitted_norm.split()
    expected_words = expected_norm.split()

    if set(submitted_words) == set(expected_words):
        return TranslationGradeResult(
            correct=False,
            score=0.7,
            expected=expected_hebrew,
            submitted=submitted,
            feedback=(
                f"You have the right words but in the wrong order. "
                f"Expected: {expected_hebrew} ({expected_transliteration})"
            ),
            transliteration=expected_transliteration,
        )

    if len(submitted_words) == len(expected_words):
        matches = sum(1 for s, e in zip(submitted_words, expected_words) if s == e)
        if matches > 0:
            score = matches / len(expected_words)
            return TranslationGradeResult(
                correct=False,
                score=score,
                expected=expected_hebrew,
                submitted=submitted,
                feedback=(
                    f"Partially correct ({int(score * 100)}%). "
                    f"Expected: {expected_hebrew} ({expected_transliteration})"
                ),
                transliteration=expected_transliteration,
            )

    return TranslationGradeResult(
        correct=False,
        score=0.0,
        expected=expected_hebrew,
        submitted=submitted,
        feedback=f"Incorrect. Expected: {expected_hebrew} ({expected_transliteration})",
        transliteration=expected_transliteration,
    )
