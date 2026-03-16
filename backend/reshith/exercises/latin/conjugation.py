"""
Latin verb conjugation exercise generator.

Supports 1st conjugation (-āre) and 2nd conjugation (-ēre),
present tense active indicative (lessons 1-2).

Conjugation uses the consonant stem:
  1st conj: amāre → stem "am" (strip -āre or -are)
  2nd conj: monēre → stem "mon" (strip -ēre)
"""

import random
import unicodedata
from dataclasses import dataclass

from reshith.exercises.latin.vocabulary import LatinWord, load_lessons_up_to


def strip_macrons(text: str) -> str:
    """Remove macrons from Latin text for comparison."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped).lower().strip()


# ── Conjugation paradigms ─────────────────────────────────────────────────────
# Endings are appended to the consonant stem.

# 1st conjugation present active indicative (amāre → stem "am")
CONJ1_PRESENT = {
    ("1", "sg"): "ō",
    ("2", "sg"): "ās",
    ("3", "sg"): "at",
    ("1", "pl"): "āmus",
    ("2", "pl"): "ātis",
    ("3", "pl"): "ant",
}

# 2nd conjugation present active indicative (monēre → stem "mon")
CONJ2_PRESENT = {
    ("1", "sg"): "eō",
    ("2", "sg"): "ēs",
    ("3", "sg"): "et",
    ("1", "pl"): "ēmus",
    ("2", "pl"): "ētis",
    ("3", "pl"): "ent",
}

PERSON_NAMES = {"1": "1st person", "2": "2nd person", "3": "3rd person"}
NUMBER_NAMES = {"sg": "singular", "pl": "plural"}
PRONOUNS = {
    ("1", "sg"): "egō",
    ("2", "sg"): "tū",
    ("3", "sg"): "is/ea/id",
    ("1", "pl"): "nōs",
    ("2", "pl"): "vōs",
    ("3", "pl"): "eī/eae/ea",
}


@dataclass
class VerbInfo:
    """Parsed information about a Latin verb."""
    word: LatinWord
    infinitive: str   # e.g. "amāre"
    stem: str         # consonant stem, e.g. "am" (1st) or "mon" (2nd)
    conjugation: str  # "1" or "2"
    definition: str


@dataclass
class ConjugationExercise:
    id: str
    dict_form: str
    definition: str
    person: str
    number: str
    prompt: str
    answer: str
    lesson: int


def _parse_verb(word: LatinWord) -> VerbInfo | None:
    """
    Parse a LatinWord into VerbInfo.
    Dictionary form: "amō, amāre" — we extract the infinitive (2nd part).
    Consonant stem = infinitive with thematic suffix stripped.
    """
    raw = word.word
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) < 2:
        return None

    infinitive = parts[1].strip()

    if infinitive.endswith("āre"):
        # 1st conjugation: strip -āre (3 chars) to get consonant stem
        stem = infinitive[:-3]
        return VerbInfo(word=word, infinitive=infinitive, stem=stem, conjugation="1", definition=word.definition)

    elif infinitive.endswith("ēre"):
        # 2nd conjugation: strip -ēre (3 chars) to get consonant stem
        stem = infinitive[:-3]
        return VerbInfo(word=word, infinitive=infinitive, stem=stem, conjugation="2", definition=word.definition)

    else:
        # Check without macrons (e.g. "dare" with no macron on ā)
        inf_clean = strip_macrons(infinitive)
        if inf_clean.endswith("are"):
            stem = infinitive[:-3]  # strip last 3 chars (-are or -āre without macron)
            return VerbInfo(word=word, infinitive=infinitive, stem=stem, conjugation="1", definition=word.definition)
        # 3rd/4th conjugation and irregulars are not supported
        return None


def _conjugate(info: VerbInfo, person: str, number: str) -> str | None:
    """Produce a conjugated form."""
    key = (person, number)

    if info.conjugation == "1":
        ending = CONJ1_PRESENT.get(key)
        return info.stem + ending if ending is not None else None

    elif info.conjugation == "2":
        ending = CONJ2_PRESENT.get(key)
        return info.stem + ending if ending is not None else None

    return None


def load_verbs(max_lesson: int, variant: str = "lat") -> list[VerbInfo]:
    words = load_lessons_up_to(max_lesson, variant)
    verbs = []
    for w in words:
        if w.category != "verbs":
            continue
        info = _parse_verb(w)
        if info is not None:
            verbs.append(info)
    return verbs


PERSONS = ["1", "2", "3"]
NUMBERS = ["sg", "pl"]


def generate_exercises(
    max_lesson: int = 2,
    count: int = 10,
    variant: str = "lat",
) -> list[ConjugationExercise]:
    verbs = load_verbs(max_lesson, variant)
    if not verbs:
        return []

    exercises = []
    for i in range(count):
        verb = random.choice(verbs)
        person = random.choice(PERSONS)
        number = random.choice(NUMBERS)

        form = _conjugate(verb, person, number)
        if form is None:
            continue

        person_name = PERSON_NAMES[person]
        number_name = NUMBER_NAMES[number]
        pronoun = PRONOUNS[(person, number)]
        # Extract a short English gloss
        gloss = verb.definition.split(";")[0].split(",")[0].strip()
        prompt = (
            f"Conjugate {verb.infinitive} ({gloss}) "
            f"— {person_name} {number_name} present active "
            f"({pronoun} ___)"
        )

        exercises.append(
            ConjugationExercise(
                id=f"conj-{i}-{strip_macrons(verb.infinitive)}-{person}-{number}",
                dict_form=verb.word.word,
                definition=verb.definition,
                person=person,
                number=number,
                prompt=prompt,
                answer=form,
                lesson=verb.word.lesson,
            )
        )

    return exercises


def grade_exercise(submitted: str, expected: str) -> tuple[bool, str]:
    """Grade a conjugation answer (macron-insensitive)."""
    correct = strip_macrons(submitted) == strip_macrons(expected)
    if correct:
        feedback = f"Correct! The form is {expected}."
    else:
        feedback = f"Not quite. The expected form is {expected}."
    return correct, feedback
