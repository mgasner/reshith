"""
Greek verb conjugation exercise generator.

Supports ω-verbs, present active indicative.
Works for both Ancient Greek (grc) and NT Koine (gnt).

Dictionary form: "λύω, λύειν"
Present stem = infinitive - "-ειν"
"""

import random
import unicodedata
from dataclasses import dataclass

from reshith.exercises.greek.vocabulary import GreekWord, load_lessons_up_to


def _norm(text: str) -> str:
    """Strip diacritics and lowercase."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    ).lower().strip()


# Present active indicative endings (appended to stem from infinitive - "-ειν")
PRES_ACT_IND = {
    ("1", "sg"): "ω",
    ("2", "sg"): "εις",
    ("3", "sg"): "ει",
    ("1", "pl"): "ομεν",
    ("2", "pl"): "ετε",
    ("3", "pl"): "ουσι",
}

PERSON_NAMES = {"1": "1st person", "2": "2nd person", "3": "3rd person"}
NUMBER_NAMES = {"sg": "singular", "pl": "plural"}
PRONOUNS = {
    ("1", "sg"): "ἐγώ",
    ("2", "sg"): "σύ",
    ("3", "sg"): "αὐτός/ή/ό",
    ("1", "pl"): "ἡμεῖς",
    ("2", "pl"): "ὑμεῖς",
    ("3", "pl"): "αὐτοί/αί/ά",
}


@dataclass
class VerbInfo:
    word: GreekWord
    inf: str    # infinitive e.g. "λύειν"
    stem: str   # present stem e.g. "λύ"
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


def _parse_verb(word: GreekWord) -> VerbInfo | None:
    """Parse "λύω, λύειν" → VerbInfo."""
    parts = [p.strip() for p in word.word.split(",")]
    if len(parts) < 2:
        return None
    inf = parts[1].strip()
    inf_norm = _norm(inf)
    if not inf_norm.endswith("ειν"):
        return None
    # Stem = infinitive minus last 3 chars ("-ειν")
    stem = inf[:-3]
    return VerbInfo(word=word, inf=inf, stem=stem, definition=word.definition)


def _conjugate(info: VerbInfo, person: str, number: str) -> str | None:
    ending = PRES_ACT_IND.get((person, number))
    return info.stem + ending if ending is not None else None


def load_verbs(max_lesson: int, variant: str = "grc") -> list[VerbInfo]:
    words = load_lessons_up_to(max_lesson, variant)
    return [
        info
        for w in words
        if w.category == "verbs"
        for info in [_parse_verb(w)]
        if info is not None
    ]


PERSONS = ["1", "2", "3"]
NUMBERS = ["sg", "pl"]


def generate_exercises(
    max_lesson: int = 2,
    count: int = 10,
    variant: str = "grc",
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
        gloss = verb.definition.split(";")[0].split(",")[0].strip()
        pronoun = PRONOUNS[(person, number)]
        exercises.append(
            ConjugationExercise(
                id=f"grc-conj-{i}-{_norm(verb.inf)}-{person}-{number}",
                dict_form=verb.word.word,
                definition=verb.definition,
                person=person,
                number=number,
                prompt=(
                    f"Conjugate {verb.inf} ({gloss}) — "
                    f"{PERSON_NAMES[person]} {NUMBER_NAMES[number]} present active "
                    f"({pronoun} ___)"
                ),
                answer=form,
                lesson=verb.word.lesson,
            )
        )
    return exercises


def grade_exercise(submitted: str, expected: str) -> tuple[bool, str]:
    correct = _norm(submitted) == _norm(expected)
    if correct:
        return True, f"Correct! The form is {expected}."
    return False, f"Not quite. The expected form is {expected}."
