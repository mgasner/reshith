"""
Latin noun declension exercise generator.

Supports 1st and 2nd declension nouns (lessons 1-2).
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


# ── Declension paradigms ──────────────────────────────────────────────────────

# 1st declension: puella, -ae (mostly feminine)
DECL1 = {
    ("nom", "sg"): "a",
    ("gen", "sg"): "ae",
    ("dat", "sg"): "ae",
    ("acc", "sg"): "am",
    ("abl", "sg"): "ā",
    ("nom", "pl"): "ae",
    ("gen", "pl"): "ārum",
    ("dat", "pl"): "īs",
    ("acc", "pl"): "ās",
    ("abl", "pl"): "īs",
}

# 2nd declension masculine: dominus, -ī
DECL2M = {
    ("nom", "sg"): "us",
    ("gen", "sg"): "ī",
    ("dat", "sg"): "ō",
    ("acc", "sg"): "um",
    ("abl", "sg"): "ō",
    ("nom", "pl"): "ī",
    ("gen", "pl"): "ōrum",
    ("dat", "pl"): "īs",
    ("acc", "pl"): "ōs",
    ("abl", "pl"): "īs",
}

# 2nd declension neuter: caelum, -ī
DECL2N = {
    ("nom", "sg"): "um",
    ("gen", "sg"): "ī",
    ("dat", "sg"): "ō",
    ("acc", "sg"): "um",
    ("abl", "sg"): "ō",
    ("nom", "pl"): "a",
    ("gen", "pl"): "ōrum",
    ("dat", "pl"): "īs",
    ("acc", "pl"): "a",
    ("abl", "pl"): "īs",
}

# 2nd declension -r: puer/ager type — stem from genitive, nom sg kept as-is
DECL2R = {
    ("nom", "sg"): None,  # use nom_sg directly
    ("gen", "sg"): "ī",
    ("dat", "sg"): "ō",
    ("acc", "sg"): "um",
    ("abl", "sg"): "ō",
    ("nom", "pl"): "ī",
    ("gen", "pl"): "ōrum",
    ("dat", "pl"): "īs",
    ("acc", "pl"): "ōs",
    ("abl", "pl"): "īs",
}

CASE_NAMES = {
    "nom": "nominative",
    "gen": "genitive",
    "dat": "dative",
    "acc": "accusative",
    "abl": "ablative",
}

NUMBER_NAMES = {"sg": "singular", "pl": "plural"}


@dataclass
class NounInfo:
    """Parsed information about a Latin noun."""
    word: LatinWord
    nom_sg: str
    stem: str
    declension: str   # "1", "2m", "2n", "2r"


@dataclass
class DeclensionExercise:
    id: str
    dict_form: str
    definition: str
    case: str
    number: str
    prompt: str
    answer: str
    lesson: int


def _parse_noun(word: LatinWord) -> NounInfo | None:
    """
    Parse a LatinWord into NounInfo.
    Handles abbreviated gen (-ae, -ī) and full gen (puerī, agrī).
    Returns None if the word cannot be parsed as a declinable noun.
    """
    raw = word.word
    parts = [p.strip() for p in raw.split(",", 1)]
    nom = parts[0].strip()

    if len(parts) < 2:
        return None

    gen_part = parts[1].strip()

    if gen_part.startswith("-"):
        gen_ending = strip_macrons(gen_part[1:])  # "ae" or "i"

        if gen_ending == "ae":
            stem = nom[:-1]  # drop final 'a'  (puella → puell)
            return NounInfo(word=word, nom_sg=nom, stem=stem, declension="1")

        elif gen_ending == "i":
            nom_clean = strip_macrons(nom)
            if nom_clean.endswith("um"):
                stem = nom[:-2]  # caelum → cael
                return NounInfo(word=word, nom_sg=nom, stem=stem, declension="2n")
            elif nom_clean.endswith("us"):
                stem = nom[:-2]  # dominus → domin
                return NounInfo(word=word, nom_sg=nom, stem=stem, declension="2m")
            else:
                return None
        else:
            return None

    else:
        # Full genitive given (e.g. "puerī", "agrī", "virī")
        gen_clean = strip_macrons(gen_part)
        if gen_clean.endswith("i"):
            stem = gen_part[:-1]  # strip final ī → "puer", "agr"
            nom_clean = strip_macrons(nom)
            if nom_clean.endswith("um"):
                return NounInfo(word=word, nom_sg=nom, stem=stem, declension="2n")
            else:
                # -r type
                return NounInfo(word=word, nom_sg=nom, stem=stem, declension="2r")
        else:
            return None


def _decline(info: NounInfo, case: str, number: str) -> str | None:
    """Produce the declined form of a noun."""
    key = (case, number)

    if info.declension == "1":
        ending = DECL1.get(key)
        return info.stem + ending if ending is not None else None

    elif info.declension == "2m":
        ending = DECL2M.get(key)
        return info.stem + ending if ending is not None else None

    elif info.declension == "2n":
        ending = DECL2N.get(key)
        return info.stem + ending if ending is not None else None

    elif info.declension == "2r":
        if key == ("nom", "sg"):
            return info.nom_sg
        ending = DECL2R.get(key)
        return info.stem + ending if ending is not None else None

    return None


def load_nouns(max_lesson: int, variant: str = "lat") -> list[NounInfo]:
    words = load_lessons_up_to(max_lesson, variant)
    nouns = []
    for w in words:
        if w.category != "nouns":
            continue
        info = _parse_noun(w)
        if info is not None:
            nouns.append(info)
    return nouns


CASES = ["nom", "gen", "dat", "acc", "abl"]
NUMBERS = ["sg", "pl"]


def generate_exercises(
    max_lesson: int = 2,
    count: int = 10,
    variant: str = "lat",
) -> list[DeclensionExercise]:
    nouns = load_nouns(max_lesson, variant)
    if not nouns:
        return []

    exercises = []
    for i in range(count):
        noun = random.choice(nouns)
        case = random.choice(CASES)
        number = random.choice(NUMBERS)

        form = _decline(noun, case, number)
        if form is None:
            continue

        case_name = CASE_NAMES[case]
        number_name = NUMBER_NAMES[number]
        prompt = (
            f"Give the {case_name} {number_name} of: "
            f"{noun.word.word} ({noun.word.definition})"
        )

        exercises.append(
            DeclensionExercise(
                id=f"decl-{i}-{strip_macrons(noun.nom_sg)}-{case}-{number}",
                dict_form=noun.word.word,
                definition=noun.word.definition,
                case=case,
                number=number,
                prompt=prompt,
                answer=form,
                lesson=noun.word.lesson,
            )
        )

    return exercises


def grade_exercise(submitted: str, expected: str) -> tuple[bool, str]:
    """Grade a declension answer (macron-insensitive)."""
    correct = strip_macrons(submitted) == strip_macrons(expected)
    if correct:
        feedback = f"Correct! The form is {expected}."
    else:
        feedback = f"Not quite. The expected form is {expected}."
    return correct, feedback
