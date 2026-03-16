"""
Advanced exercise generator for Biblical Hebrew (Lesson 5+).

Generates exercises for:
- Comparative constructions with מִן (min-): "X is [adj]-er than Y"
- Relative clauses with אֲשֶׁר (ʾăšer): "the X who/which..."
- Adjective-noun combinations
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
class Adjective:
    hebrew: str
    transliteration: str
    definition: str
    lesson: int


@dataclass
class ComparativeExercise:
    """A Hebrew comparative construction exercise."""

    pattern: str
    hebrew: str
    transliteration: str
    english_answer: str
    components: dict[str, str]
    lesson: int = 1


@dataclass
class ComparativeGradeResult:
    """Result of grading a comparative exercise."""

    correct: bool
    score: float
    expected: str
    submitted: str
    feedback: str


@dataclass
class RelativeClauseExercise:
    """A Hebrew relative clause exercise with אֲשֶׁר."""

    pattern: str
    hebrew: str
    transliteration: str
    english_answer: str
    components: dict[str, str]
    lesson: int = 1


def load_adjectives(max_lesson: int) -> list[Adjective]:
    """Load adjectives from vocabulary up to max_lesson."""
    vocab = load_lessons_up_to(max_lesson)
    return [
        Adjective(
            hebrew=item.hebrew,
            transliteration=item.transliteration,
            definition=item.definition,
            lesson=item.lesson,
        )
        for item in vocab
        if item.category == "adjectives"
    ]


def load_min_preposition(max_lesson: int) -> tuple[str, str] | None:
    """Load the מִן preposition if available."""
    vocab = load_lessons_up_to(max_lesson)
    for item in vocab:
        if item.hebrew == "מִן":
            return item.hebrew, item.transliteration
    return None


def load_asher_pronoun(max_lesson: int) -> tuple[str, str] | None:
    """Load the אֲשֶׁר relative pronoun if available."""
    vocab = load_lessons_up_to(max_lesson)
    for item in vocab:
        if item.hebrew == "אֲשֶׁר":
            return item.hebrew, item.transliteration
    return None


def attach_min_preposition(
    noun_hebrew: str,
    noun_transliteration: str,
    has_article: bool = False,
) -> tuple[str, str]:
    """
    Attach the מִן preposition to a noun.

    Rules:
    - Before the article: מִן + הַ → מֵהַ (assimilation with compensatory lengthening)
    - Before regular consonants: מִן assimilates, doubling the following consonant
    - Before gutturals: מֵ (compensatory lengthening, no doubling)

    For simplicity in exercises, we use the common patterns:
    - מִן + הַנָּשִׁים → מֵהַנָּשִׁים (from the women)
    - מִן + אִישׁ → מֵאִישׁ (from a man)
    """
    gutturals = {"א", "ה", "ח", "ע", "ר"}

    first_char = ""
    for char in noun_hebrew:
        if "\u05D0" <= char <= "\u05EA":
            first_char = char
            break

    if has_article and noun_hebrew.startswith("הַ"):
        result_heb = "מֵ" + noun_hebrew
        result_trans = "mē" + noun_transliteration
        return result_heb, result_trans

    if has_article and noun_hebrew.startswith("הָ"):
        result_heb = "מֵ" + noun_hebrew
        result_trans = "mē" + noun_transliteration
        return result_heb, result_trans

    if first_char in gutturals:
        result_heb = "מֵ" + noun_hebrew
        result_trans = "mē" + noun_transliteration
        return result_heb, result_trans

    dagesh = "\u05BC"
    if first_char and first_char not in gutturals:
        if dagesh not in noun_hebrew[:3]:
            result_heb = "מִ" + first_char + dagesh + noun_hebrew[len(first_char):]
        else:
            result_heb = "מִ" + noun_hebrew
        result_trans = "mi" + noun_transliteration
        return result_heb, result_trans

    return "מִן־" + noun_hebrew, "min-" + noun_transliteration


def _get_comparative_cache_key(
    adjectives: list[Adjective],
    nouns: list[Noun],
) -> str:
    """Generate a cache key for comparative mappings."""
    adj_ids = sorted([a.transliteration for a in adjectives])
    noun_ids = sorted([n.transliteration for n in nouns])
    content = json.dumps({"adjectives": adj_ids, "nouns": noun_ids})
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_comparative_cache_path(cache_key: str) -> Path:
    """Get the cache file path for comparative mappings."""
    return CACHE_DIR / f"comparative_map_{cache_key}.json"


async def generate_comparative_mappings(
    adjectives: list[Adjective],
    nouns: list[Noun],
    force_refresh: bool = False,
) -> dict:
    """
    Generate mappings for adjective-noun comparative relationships using LLM.

    Returns:
        Dict with adjective transliterations mapping to lists of noun pairs
        that make semantic sense for comparison.
        e.g., {"yāqār": [["zāhāḇ", "késep̄"], ["ḥoḵmāh", "zāhāḇ"]]}
    """
    cache_key = _get_comparative_cache_key(adjectives, nouns)
    cache_path = _get_comparative_cache_path(cache_key)

    if not force_refresh and cache_path.exists():
        logger.debug(f"Loading comparative mappings from cache: {cache_key}")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not set, using fallback comparative mappings")
        return _generate_fallback_comparative_mappings(adjectives, nouns)

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    adj_list = [f"{a.transliteration} ({a.definition})" for a in adjectives]
    noun_list = [f"{n.transliteration} ({n.definition})" for n in nouns]

    prompt = (
        "Given these Biblical Hebrew adjectives and nouns, determine which noun pairs "
        "make semantic sense for comparative constructions.\n\n"
        "For example, 'gold is more precious than silver' makes sense, "
        "but 'gold is more precious than wisdom' is debatable.\n\n"
        f"Adjectives:\n{chr(10).join(f'- {a}' for a in adj_list)}\n\n"
        f"Nouns:\n{chr(10).join(f'- {n}' for n in noun_list)}\n\n"
        "For each adjective, list pairs of nouns [A, B] where 'A is more [adj] than B' "
        "makes semantic sense. Consider:\n"
        "- Physical properties (gold vs silver for 'precious')\n"
        "- Abstract qualities (wisdom vs counsel for 'precious')\n"
        "- Moral qualities (righteous man vs evil man)\n\n"
        "Return ONLY a JSON object:\n"
        "{\n"
        '  "adjective_translit": [["noun1", "noun2"], ["noun3", "noun4"]]\n'
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
                        "sensible comparative constructions for language learning."
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

        logger.info(f"Generated and cached comparative mappings: {cache_key}")
        return result

    except Exception as e:
        logger.error(f"Failed to generate comparative mappings: {e}")
        return _generate_fallback_comparative_mappings(adjectives, nouns)


def _generate_fallback_comparative_mappings(
    adjectives: list[Adjective],
    nouns: list[Noun],
) -> dict:
    """Generate simple fallback comparative mappings when LLM is unavailable."""
    result: dict[str, list[list[str]]] = {}

    value_nouns = []
    abstract_nouns = []
    other_nouns = []

    value_words = ["gold", "silver", "money"]
    abstract_words = ["wisdom", "counsel", "advice", "work"]

    for noun in nouns:
        defn = noun.definition.lower()
        if any(word in defn for word in value_words):
            value_nouns.append(noun.transliteration)
        elif any(word in defn for word in abstract_words):
            abstract_nouns.append(noun.transliteration)
        else:
            other_nouns.append(noun.transliteration)

    for adj in adjectives:
        adj_trans = adj.transliteration
        defn = adj.definition.lower()

        pairs: list[list[str]] = []

        if "precious" in defn and len(value_nouns) >= 2:
            for i, n1 in enumerate(value_nouns):
                for n2 in value_nouns[i + 1:]:
                    pairs.append([n1, n2])
            for n1 in abstract_nouns:
                for n2 in value_nouns:
                    pairs.append([n1, n2])

        elif any(word in defn for word in ["righteous", "just", "upright", "evil", "bad"]):
            pass

        if not pairs and len(nouns) >= 2:
            noun_trans = [n.transliteration for n in nouns]
            for i in range(min(3, len(noun_trans))):
                for j in range(i + 1, min(4, len(noun_trans))):
                    pairs.append([noun_trans[i], noun_trans[j]])

        result[adj_trans] = pairs

    return result


def _get_english_adjective(adj: Adjective) -> str:
    """Extract the primary English meaning from an adjective definition."""
    return adj.definition.split(",")[0].strip().lower()


def _get_english_noun(noun: Noun) -> str:
    """Extract the primary English meaning from a noun definition."""
    return noun.definition.split(",")[0].strip().lower()


def _get_comparative_english(adj_eng: str) -> str:
    """Convert an adjective to its comparative form."""
    if adj_eng.endswith("y"):
        return adj_eng[:-1] + "ier"
    elif adj_eng.endswith("e"):
        return adj_eng + "r"
    elif len(adj_eng) <= 6:
        return adj_eng + "er"
    else:
        return "more " + adj_eng


async def generate_comparative_exercise(
    adjectives: list[Adjective],
    nouns: list[Noun],
    comparative_mappings: dict,
) -> ComparativeExercise | None:
    """
    Generate a comparative construction exercise.

    Pattern: "X is [adj]-er than Y" → "X [adj] מִן־Y"
    Hebrew word order: Subject + Adjective + מִן + Compared-noun
    """
    valid_adjs = [
        a for a in adjectives
        if a.transliteration in comparative_mappings
        and comparative_mappings[a.transliteration]
    ]
    if not valid_adjs:
        return None

    adj = random.choice(valid_adjs)
    pairs = comparative_mappings[adj.transliteration]
    if not pairs:
        return None

    pair = random.choice(pairs)
    if len(pair) < 2:
        return None

    noun1_trans, noun2_trans = pair[0], pair[1]
    noun1 = next((n for n in nouns if n.transliteration == noun1_trans), None)
    noun2 = next((n for n in nouns if n.transliteration == noun2_trans), None)

    if not noun1 or not noun2:
        return None

    noun1_def_heb, noun1_def_trans, _ = add_definite_article(noun1)

    min_phrase_heb, min_phrase_trans = attach_min_preposition(
        noun2.hebrew, noun2.transliteration, has_article=False
    )

    hebrew = f"{noun1_def_heb} {adj.hebrew} {min_phrase_heb}."
    translit = f"{noun1_def_trans} {adj.transliteration} {min_phrase_trans}."

    adj_eng = _get_english_adjective(adj)
    noun1_eng = _get_english_noun(noun1)
    noun2_eng = _get_english_noun(noun2)
    comp_adj = _get_comparative_english(adj_eng)

    english = f"The {noun1_eng} is {comp_adj} than {noun2_eng}."

    return ComparativeExercise(
        pattern="comparative_min",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "subject": noun1.hebrew,
            "adjective": adj.hebrew,
            "compared_noun": noun2.hebrew,
            "preposition": "מִן",
        },
        lesson=max(adj.lesson, noun1.lesson, noun2.lesson),
    )


async def generate_relative_clause_exercise(
    nouns: list[Noun],
    adjectives: list[Adjective],
) -> RelativeClauseExercise | None:
    """
    Generate a relative clause exercise with אֲשֶׁר.

    Pattern: "the X who/which is [adj]" → "הַX אֲשֶׁר [adj]"
    """
    if not nouns or not adjectives:
        return None

    noun = random.choice(nouns)
    adj = random.choice(adjectives)

    noun_def_heb, noun_def_trans, _ = add_definite_article(noun)

    hebrew = f"{noun_def_heb} אֲשֶׁר {adj.hebrew}."
    translit = f"{noun_def_trans} ʾăšer {adj.transliteration}."

    noun_eng = _get_english_noun(noun)
    adj_eng = _get_english_adjective(adj)

    english = f"The {noun_eng} who is {adj_eng}."

    return RelativeClauseExercise(
        pattern="relative_asher",
        hebrew=hebrew,
        transliteration=translit,
        english_answer=english,
        components={
            "noun": noun.hebrew,
            "relative_pronoun": "אֲשֶׁר",
            "adjective": adj.hebrew,
        },
        lesson=max(noun.lesson, adj.lesson),
    )


async def generate_comparative_exercises(
    max_lesson: int = 5,
    count: int = 10,
) -> list[ComparativeExercise]:
    """
    Generate comparative construction exercises.

    Args:
        max_lesson: Include vocabulary up to this lesson (must be >= 5 for adjectives)
        count: Number of exercises to generate

    Returns:
        List of ComparativeExercise objects
    """
    adjectives = load_adjectives(max_lesson)
    nouns = load_nouns_for_exercises(max_lesson)

    if not adjectives or not nouns:
        return []

    comparative_mappings = await generate_comparative_mappings(adjectives, nouns)

    exercises: list[ComparativeExercise] = []
    attempts = 0
    max_attempts = count * 3

    while len(exercises) < count and attempts < max_attempts:
        attempts += 1
        exercise = await generate_comparative_exercise(
            adjectives, nouns, comparative_mappings
        )
        if exercise:
            exercises.append(exercise)

    return exercises


async def generate_relative_clause_exercises(
    max_lesson: int = 5,
    count: int = 10,
) -> list[RelativeClauseExercise]:
    """
    Generate relative clause exercises with אֲשֶׁר.

    Args:
        max_lesson: Include vocabulary up to this lesson (must be >= 5 for אֲשֶׁר)
        count: Number of exercises to generate

    Returns:
        List of RelativeClauseExercise objects
    """
    asher = load_asher_pronoun(max_lesson)
    if not asher:
        return []

    nouns = load_nouns_for_exercises(max_lesson)
    adjectives = load_adjectives(max_lesson)

    if not nouns or not adjectives:
        return []

    exercises: list[RelativeClauseExercise] = []
    attempts = 0
    max_attempts = count * 3

    while len(exercises) < count and attempts < max_attempts:
        attempts += 1
        exercise = await generate_relative_clause_exercise(nouns, adjectives)
        if exercise:
            exercises.append(exercise)

    return exercises


def normalize_english_for_grading(text: str) -> str:
    """Normalize English text for comparison during grading."""
    normalized = text.strip().lower()
    normalized = normalized.replace("  ", " ")
    normalized = normalized.rstrip(".?!")
    return normalized


def grade_comparative_exercise(
    submitted: str,
    expected_english: str,
) -> ComparativeGradeResult:
    """
    Grade a Hebrew-to-English comparative translation.

    Args:
        submitted: Student's English answer
        expected_english: Correct English answer

    Returns:
        ComparativeGradeResult with score and feedback
    """
    submitted_norm = normalize_english_for_grading(submitted)
    expected_norm = normalize_english_for_grading(expected_english)

    if submitted_norm == expected_norm:
        return ComparativeGradeResult(
            correct=True,
            score=1.0,
            expected=expected_english,
            submitted=submitted,
            feedback="Correct!",
        )

    if "than" in submitted_norm and "than" in expected_norm:
        submitted_words = submitted_norm.split()
        expected_words = expected_norm.split()

        matches = sum(1 for w in submitted_words if w in expected_words)
        if matches >= len(expected_words) - 2:
            return ComparativeGradeResult(
                correct=False,
                score=0.8,
                expected=expected_english,
                submitted=submitted,
                feedback=f"Almost correct. Expected: {expected_english}",
            )

    score = 0.0
    if "than" in submitted_norm:
        score += 0.3
    if any(word in submitted_norm for word in ["more", "er"]):
        score += 0.2

    return ComparativeGradeResult(
        correct=False,
        score=min(score, 0.7),
        expected=expected_english,
        submitted=submitted,
        feedback=f"Incorrect. Expected: {expected_english}",
    )


def grade_relative_clause_exercise(
    submitted: str,
    expected_english: str,
) -> ComparativeGradeResult:
    """
    Grade a Hebrew-to-English relative clause translation.

    Args:
        submitted: Student's English answer
        expected_english: Correct English answer

    Returns:
        ComparativeGradeResult with score and feedback
    """
    submitted_norm = normalize_english_for_grading(submitted)
    expected_norm = normalize_english_for_grading(expected_english)

    if submitted_norm == expected_norm:
        return ComparativeGradeResult(
            correct=True,
            score=1.0,
            expected=expected_english,
            submitted=submitted,
            feedback="Correct!",
        )

    relative_words = ["who", "which", "that"]
    has_relative = any(word in submitted_norm for word in relative_words)

    if has_relative:
        submitted_words = submitted_norm.split()
        expected_words = expected_norm.split()

        matches = sum(1 for w in submitted_words if w in expected_words)
        if matches >= len(expected_words) - 2:
            return ComparativeGradeResult(
                correct=True,
                score=1.0,
                expected=expected_english,
                submitted=submitted,
                feedback="Correct! (Acceptable variation)",
            )

        if matches >= len(expected_words) - 3:
            return ComparativeGradeResult(
                correct=False,
                score=0.8,
                expected=expected_english,
                submitted=submitted,
                feedback=f"Almost correct. Expected: {expected_english}",
            )

    score = 0.0
    if has_relative:
        score += 0.4

    return ComparativeGradeResult(
        correct=False,
        score=min(score, 0.7),
        expected=expected_english,
        submitted=submitted,
        feedback=f"Incorrect. Expected: {expected_english}",
    )
