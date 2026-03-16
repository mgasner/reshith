"""
Preposition exercise generator and grader for Biblical Hebrew.

Handles the inseparable prepositions בְּ (in), לְ (to), and כְּ (like/as)
prefixed to nouns.
"""

import json
import random
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Preposition(Enum):
    BE = "bə"      # בְּ - in, with, by means of
    LE = "lə"      # לְ - to, for
    KE = "kə"      # כְּ - like, as


@dataclass
class Noun:
    hebrew: str
    transliteration: str
    definition: str
    category: str
    lesson: int = 1

    @property
    def starts_with_bgdkpt(self) -> bool:
        """Check if noun starts with a begadkephat letter."""
        if not self.hebrew:
            return False
        first_char = self.hebrew[0]
        return first_char in "בגדכפת"

    @property
    def starts_with_shewa(self) -> bool:
        """Check if the noun starts with a shewa (vocal or silent)."""
        if len(self.hebrew) < 2:
            return False
        return "\u05b0" in self.hebrew[:3]

    @property
    def has_initial_yod_with_shewa(self) -> bool:
        """Check if noun starts with yod + shewa (יְ)."""
        return self.hebrew.startswith("יְ")

    @property
    def first_vowel_is_hatep(self) -> bool:
        """Check if first vowel is a hatep vowel."""
        for char in self.hebrew[1:4]:
            code = ord(char)
            if code in (0x05B2, 0x05B3, 0x05B1):
                return True
            if 0x05B0 <= code <= 0x05BD:
                return False
        return False


@dataclass
class PrepositionalPhrase:
    preposition: Preposition
    noun: Noun
    hebrew: str
    transliteration: str
    english: str
    lesson: int = 1


PREPOSITION_DATA = {
    Preposition.BE: {
        "hebrew": "בְּ",
        "english": ["in", "with", "by means of"],
        "primary_english": "in",
    },
    Preposition.LE: {
        "hebrew": "לְ",
        "english": ["to", "for"],
        "primary_english": "to",
    },
    Preposition.KE: {
        "hebrew": "כְּ",
        "english": ["like", "as"],
        "primary_english": "like",
    },
}


def get_preposition_hebrew(prep: Preposition, noun: Noun) -> str:
    """
    Get the correct Hebrew form when prefixing a preposition to a noun.

    Rules (simplified from Lambdin §15):
    1. Before bgdkpt with dagesh: בְּבַיִת -> בְּבַיִת (dagesh remains)
    2. Before shewa: the preposition takes hireq instead of shewa
       בְּ + דְּבָרִים -> בִּדְבָרִים
    3. Before hatep vowel: preposition takes corresponding short vowel
       לְ + אֱלֹהִים -> לֵאלֹהִים
    4. Before yod with shewa: contraction to י + hireq
       לְ + יְהוּדָה -> לִיהוּדָה
    """
    base_prep = PREPOSITION_DATA[prep]["hebrew"]
    prep_consonant = base_prep[0]

    noun_hebrew = noun.hebrew

    if noun.first_vowel_is_hatep:
        for i, char in enumerate(noun_hebrew):
            code = ord(char)
            if code == 0x05B2:
                return prep_consonant + "\u05B7" + noun_hebrew
            elif code == 0x05B3:
                return prep_consonant + "\u05B8" + noun_hebrew
            elif code == 0x05B1:
                return prep_consonant + "\u05B6" + noun_hebrew

    if noun.has_initial_yod_with_shewa:
        return prep_consonant + "\u05B4" + noun_hebrew[1:]

    if noun.starts_with_shewa:
        return prep_consonant + "\u05B4" + noun_hebrew

    return base_prep + noun_hebrew


def get_preposition_transliteration(prep: Preposition, noun: Noun) -> str:
    """
    Get the transliteration of a prepositional phrase.
    """
    prep_trans = prep.value

    noun_trans = noun.transliteration

    if noun.first_vowel_is_hatep:
        if "ḥa" in noun_trans[:3] or "ʾa" in noun_trans[:3]:
            prep_trans = prep_trans[0] + "a"
        elif "ḥo" in noun_trans[:3] or "ʾo" in noun_trans[:3]:
            prep_trans = prep_trans[0] + "o" if prep == Preposition.LE else prep_trans[0] + "o"
        elif "ḥe" in noun_trans[:3] or "ʾe" in noun_trans[:3]:
            prep_trans = prep_trans[0] + "e"

    if noun.has_initial_yod_with_shewa:
        prep_trans = prep_trans[0] + "î"
        if noun_trans.startswith("yə"):
            noun_trans = noun_trans[2:]

    if noun.starts_with_shewa and not noun.first_vowel_is_hatep:
        prep_trans = prep_trans[0] + "i"

    return prep_trans + noun_trans


def generate_phrase(prep: Preposition, noun: Noun) -> PrepositionalPhrase:
    """Generate a prepositional phrase from a preposition and noun."""
    hebrew = get_preposition_hebrew(prep, noun)
    transliteration = get_preposition_transliteration(prep, noun)

    primary_eng = PREPOSITION_DATA[prep]["primary_english"]

    if "the " in noun.definition.lower():
        english = f"{primary_eng} the {noun.definition.split(',')[0].lower()}"
    else:
        english = f"{primary_eng} a {noun.definition.split(',')[0].lower()}"

    return PrepositionalPhrase(
        preposition=prep,
        noun=noun,
        hebrew=hebrew,
        transliteration=transliteration,
        english=english,
        lesson=noun.lesson,
    )


def load_nouns_from_lesson(lesson_path: Path) -> list[Noun]:
    """Load nouns from a lesson JSON file."""
    with open(lesson_path, encoding="utf-8") as f:
        data = json.load(f)

    nouns = []
    for card in data.get("cards", []):
        if card.get("category") == "nouns":
            nouns.append(
                Noun(
                    hebrew=card["hebrew"],
                    transliteration=card["transliteration"],
                    definition=card["definition"],
                    category=card["category"],
                )
            )
    return nouns


def load_nouns_up_to_lesson(max_lesson: int) -> list[Noun]:
    """Load nouns from all lessons up to and including max_lesson."""
    from reshith.exercises.vocabulary import load_nouns_up_to

    vocab_items = load_nouns_up_to(max_lesson)
    return [
        Noun(
            hebrew=item.hebrew,
            transliteration=item.transliteration,
            definition=item.definition,
            category=item.category,
            lesson=item.lesson,
        )
        for item in vocab_items
    ]



def generate_exercises(
    nouns: list[Noun],
    prepositions: list[Preposition] | None = None,
    count: int = 10,
) -> list[PrepositionalPhrase]:
    """Generate a set of prepositional phrase exercises."""
    if prepositions is None:
        prepositions = list(Preposition)

    exercises = []
    for _ in range(count):
        noun = random.choice(nouns)
        prep = random.choice(prepositions)
        exercises.append(generate_phrase(prep, noun))

    return exercises


def normalize_hebrew(text: str) -> str:
    """Normalize Hebrew text for comparison (remove cantillation, normalize unicode)."""
    text = unicodedata.normalize("NFC", text)
    result = []
    for char in text:
        code = ord(char)
        if 0x0591 <= code <= 0x05AF:
            continue
        result.append(char)
    return "".join(result).strip()


def normalize_english(text: str) -> str:
    """Normalize English text for comparison."""
    text = text.lower().strip()
    text = text.replace("the ", "").replace("a ", "").replace("an ", "")
    return text


@dataclass
class GradeResult:
    correct: bool
    expected: str
    submitted: str
    feedback: str


def grade_hebrew_to_english(
    phrase: PrepositionalPhrase,
    submitted: str,
) -> GradeResult:
    """Grade an English translation of a Hebrew prepositional phrase."""
    submitted_norm = normalize_english(submitted)
    expected_norm = normalize_english(phrase.english)

    prep_data = PREPOSITION_DATA[phrase.preposition]
    noun_def = phrase.noun.definition.split(",")[0].lower().strip()

    correct = False
    for prep_eng in prep_data["english"]:
        if prep_eng in submitted_norm and noun_def in submitted_norm:
            correct = True
            break

    if submitted_norm == expected_norm:
        correct = True

    if correct:
        feedback = "Correct!"
    else:
        feedback = f"Expected something like: '{phrase.english}'"

    return GradeResult(
        correct=correct,
        expected=phrase.english,
        submitted=submitted,
        feedback=feedback,
    )


def grade_english_to_hebrew(
    phrase: PrepositionalPhrase,
    submitted: str,
) -> GradeResult:
    """Grade a Hebrew translation of an English prepositional phrase."""
    submitted_norm = normalize_hebrew(submitted)
    expected_norm = normalize_hebrew(phrase.hebrew)

    correct = submitted_norm == expected_norm

    if correct:
        feedback = "Correct!"
    else:
        feedback = f"Expected: {phrase.hebrew} ({phrase.transliteration})"

    return GradeResult(
        correct=correct,
        expected=phrase.hebrew,
        submitted=submitted,
        feedback=feedback,
    )


@dataclass
class Exercise:
    phrase: PrepositionalPhrase
    direction: str
    prompt: str
    answer: str


def create_exercise(
    phrase: PrepositionalPhrase,
    direction: str = "hebrew_to_english",
) -> Exercise:
    """Create an exercise from a prepositional phrase."""
    if direction == "hebrew_to_english":
        prompt = phrase.hebrew
        answer = phrase.english
    else:
        prompt = phrase.english
        answer = phrase.hebrew

    return Exercise(
        phrase=phrase,
        direction=direction,
        prompt=prompt,
        answer=answer,
    )


def grade_exercise(exercise: Exercise, submitted: str) -> GradeResult:
    """Grade a submitted answer for an exercise."""
    if exercise.direction == "hebrew_to_english":
        return grade_hebrew_to_english(exercise.phrase, submitted)
    else:
        return grade_english_to_hebrew(exercise.phrase, submitted)
