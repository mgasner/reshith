"""
Definite article exercise generator for Biblical Hebrew.

Handles the definite article הַ with its phonological variations
before different consonant types.
"""

import random
import unicodedata
from dataclasses import dataclass
from enum import Enum

from reshith.exercises.vocabulary import load_lessons_up_to


class ArticleType(Enum):
    REGULAR = "regular"
    GUTTURAL_COMPENSATORY = "guttural_compensatory"
    GUTTURAL_VIRTUAL = "guttural_virtual"
    HE_HET = "he_het"


GUTTURALS = {"א", "ה", "ח", "ע"}
RESH = "ר"


@dataclass
class Noun:
    hebrew: str
    transliteration: str
    definition: str
    category: str
    lesson: int

    @property
    def first_consonant(self) -> str:
        """Get the first consonant (base letter without points)."""
        for char in self.hebrew:
            if "\u05D0" <= char <= "\u05EA":
                return char
        return ""

    @property
    def is_guttural_initial(self) -> bool:
        """Check if noun starts with a guttural consonant."""
        return self.first_consonant in GUTTURALS

    @property
    def is_resh_initial(self) -> bool:
        """Check if noun starts with resh."""
        return self.first_consonant == RESH

    @property
    def first_vowel(self) -> str | None:
        """Get the first vowel point after the initial consonant."""
        found_consonant = False
        for char in self.hebrew:
            if "\u05D0" <= char <= "\u05EA":
                if found_consonant:
                    return None
                found_consonant = True
            elif found_consonant and "\u05B0" <= char <= "\u05BD":
                return char
        return None

    @property
    def has_qamets_or_patah(self) -> bool:
        """Check if first vowel is qamets (ָ) or patah (ַ)."""
        vowel = self.first_vowel
        return vowel in ("\u05B7", "\u05B8")

    @property
    def has_hatep_vowel(self) -> bool:
        """Check if first vowel is a hatep vowel."""
        vowel = self.first_vowel
        return vowel in ("\u05B1", "\u05B2", "\u05B3")


@dataclass
class ArticlePhrase:
    noun: Noun
    article_type: ArticleType
    hebrew_indefinite: str
    hebrew_definite: str
    transliteration_indefinite: str
    transliteration_definite: str
    english_indefinite: str
    english_definite: str


def add_definite_article(noun: Noun) -> tuple[str, str, ArticleType]:
    """
    Add the definite article to a noun following Hebrew phonological rules.

    Rules (from Lambdin §14, §18, §21):
    1. Regular: הַ + dagesh in following consonant (before non-gutturals)
    2. Before gutturals with qamets/patah: הָ (compensatory lengthening)
    3. Before ח/ע with qamets: הֶ (virtual doubling)
    4. Before ה/ח with hatep: הַ (no change)
    5. Before ר: usually הָ

    Returns:
        Tuple of (hebrew_with_article, transliteration_with_article, article_type)
    """
    hebrew = noun.hebrew
    first_cons = noun.first_consonant

    if noun.is_resh_initial:
        hebrew_def = "הָ" + hebrew
        trans_def = "hā" + noun.transliteration
        return hebrew_def, trans_def, ArticleType.GUTTURAL_COMPENSATORY

    if noun.is_guttural_initial:
        if noun.has_hatep_vowel:
            hebrew_def = "הַ" + hebrew
            trans_def = "ha" + noun.transliteration
            return hebrew_def, trans_def, ArticleType.REGULAR

        if first_cons in ("ח", "ע") and noun.has_qamets_or_patah:
            hebrew_def = "הֶ" + hebrew
            trans_def = "he" + noun.transliteration
            return hebrew_def, trans_def, ArticleType.GUTTURAL_VIRTUAL

        hebrew_def = "הָ" + hebrew
        trans_def = "hā" + noun.transliteration
        return hebrew_def, trans_def, ArticleType.GUTTURAL_COMPENSATORY

    dagesh = "\u05BC"
    if first_cons in "בגדכפת":
        if dagesh not in hebrew[:3]:
            hebrew_def = "הַ" + first_cons + dagesh + hebrew[len(first_cons) :]
        else:
            hebrew_def = "הַ" + hebrew
    else:
        hebrew_def = "הַ" + hebrew

    trans_def = "ha" + noun.transliteration
    return hebrew_def, trans_def, ArticleType.REGULAR


def generate_article_phrase(noun: Noun) -> ArticlePhrase:
    """Generate an article phrase exercise from a noun."""
    hebrew_def, trans_def, article_type = add_definite_article(noun)

    definition_base = noun.definition.split(",")[0].strip().lower()
    if definition_base.startswith("a ") or definition_base.startswith("an "):
        definition_base = definition_base[2:].strip()
        if definition_base.startswith(" "):
            definition_base = definition_base[1:]

    english_indef = f"a {definition_base}"
    english_def = f"the {definition_base}"

    return ArticlePhrase(
        noun=noun,
        article_type=article_type,
        hebrew_indefinite=noun.hebrew,
        hebrew_definite=hebrew_def,
        transliteration_indefinite=noun.transliteration,
        transliteration_definite=trans_def,
        english_indefinite=english_indef,
        english_definite=english_def,
    )


def load_nouns_for_exercises(max_lesson: int) -> list[Noun]:
    """Load nouns suitable for article exercises from lessons up to max_lesson."""
    vocab_items = load_lessons_up_to(max_lesson)
    nouns = []
    for item in vocab_items:
        if item.category == "nouns":
            nouns.append(
                Noun(
                    hebrew=item.hebrew,
                    transliteration=item.transliteration,
                    definition=item.definition,
                    category=item.category,
                    lesson=item.lesson,
                )
            )
    return nouns


def generate_article_exercises(
    max_lesson: int = 1,
    count: int = 10,
    include_types: list[ArticleType] | None = None,
) -> list[ArticlePhrase]:
    """
    Generate definite article exercises.

    Args:
        max_lesson: Include vocabulary up to this lesson
        count: Number of exercises to generate
        include_types: Filter to specific article types (for targeted practice)

    Returns:
        List of ArticlePhrase exercises
    """
    nouns = load_nouns_for_exercises(max_lesson)

    if not nouns:
        return []

    exercises = []
    for _ in range(count):
        noun = random.choice(nouns)
        phrase = generate_article_phrase(noun)

        if include_types and phrase.article_type not in include_types:
            continue

        exercises.append(phrase)

    return exercises


def normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for comparison."""
    text = unicodedata.normalize("NFC", text)
    result = []
    for char in text:
        code = ord(char)
        if 0x0591 <= code <= 0x05AF:
            continue
        result.append(char)
    return "".join(result).strip()


@dataclass
class GradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


def grade_indefinite_to_definite(
    phrase: ArticlePhrase,
    submitted: str,
) -> GradeResult:
    """Grade a definite form submission given an indefinite noun."""
    submitted_norm = normalize_hebrew(submitted)
    expected_norm = normalize_hebrew(phrase.hebrew_definite)

    correct = submitted_norm == expected_norm

    if correct:
        feedback = "Correct!"
    else:
        feedback = f"Expected: {phrase.hebrew_definite} ({phrase.transliteration_definite})"

    return GradeResult(
        correct=correct,
        expected=phrase.hebrew_definite,
        submitted=submitted,
        feedback=feedback,
    )


def grade_definite_to_indefinite(
    phrase: ArticlePhrase,
    submitted: str,
) -> GradeResult:
    """Grade an indefinite form submission given a definite noun."""
    submitted_norm = normalize_hebrew(submitted)
    expected_norm = normalize_hebrew(phrase.hebrew_indefinite)

    correct = submitted_norm == expected_norm

    if correct:
        feedback = "Correct!"
    else:
        feedback = f"Expected: {phrase.hebrew_indefinite} ({phrase.transliteration_indefinite})"

    return GradeResult(
        correct=correct,
        expected=phrase.hebrew_indefinite,
        submitted=submitted,
        feedback=feedback,
    )


@dataclass
class ArticleExercise:
    phrase: ArticlePhrase
    direction: str
    prompt: str
    prompt_transliteration: str
    answer: str
    answer_transliteration: str


def create_article_exercise(
    phrase: ArticlePhrase,
    direction: str = "indefinite_to_definite",
) -> ArticleExercise:
    """Create an exercise from an article phrase."""
    if direction == "indefinite_to_definite":
        prompt = phrase.hebrew_indefinite
        prompt_trans = phrase.transliteration_indefinite
        answer = phrase.hebrew_definite
        answer_trans = phrase.transliteration_definite
    else:
        prompt = phrase.hebrew_definite
        prompt_trans = phrase.transliteration_definite
        answer = phrase.hebrew_indefinite
        answer_trans = phrase.transliteration_indefinite

    return ArticleExercise(
        phrase=phrase,
        direction=direction,
        prompt=prompt,
        prompt_transliteration=prompt_trans,
        answer=answer,
        answer_transliteration=answer_trans,
    )
