"""
Greek noun declension exercise generator.

Supports:
  2nd declension masculine (-ος, -ου)
  2nd declension neuter   (-ον, -ου)
  1st declension η-type   (-ή/-η, -ῆς/-ης)
  1st declension α-type   (-α,   -ας/-ᾶς)

Works for both Ancient Greek (grc) and NT Koine (gnt).
"""

import random
import unicodedata
from dataclasses import dataclass

from reshith.exercises.greek.vocabulary import GreekWord, load_lessons_up_to


def _norm(text: str) -> str:
    """Strip all diacritical marks and lowercase — for comparison."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    ).lower().strip()


# ── Paradigm tables ───────────────────────────────────────────────────────────

DECL2M = {
    ("nom", "sg"): "ος",  ("nom", "pl"): "οι",
    ("gen", "sg"): "ου",  ("gen", "pl"): "ων",
    ("dat", "sg"): "ῳ",   ("dat", "pl"): "οις",
    ("acc", "sg"): "ον",  ("acc", "pl"): "ους",
    ("voc", "sg"): "ε",   ("voc", "pl"): "οι",
}

DECL2N = {
    ("nom", "sg"): "ον",  ("nom", "pl"): "α",
    ("gen", "sg"): "ου",  ("gen", "pl"): "ων",
    ("dat", "sg"): "ῳ",   ("dat", "pl"): "οις",
    ("acc", "sg"): "ον",  ("acc", "pl"): "α",
    ("voc", "sg"): "ον",  ("voc", "pl"): "α",
}

# 1st declension η-type (ψυχή, ψυχῆς) — η throughout singular
DECL1H = {
    ("nom", "sg"): "ή",   ("nom", "pl"): "αί",
    ("gen", "sg"): "ῆς",  ("gen", "pl"): "ῶν",
    ("dat", "sg"): "ῇ",   ("dat", "pl"): "αῖς",
    ("acc", "sg"): "ήν",  ("acc", "pl"): "άς",
    ("voc", "sg"): "ή",   ("voc", "pl"): "αί",
}

# 1st declension α-type (χώρα, χώρας) — pure α after ε/ι/ρ in Attic; used in Koine generally
DECL1A = {
    ("nom", "sg"): "α",   ("nom", "pl"): "αι",
    ("gen", "sg"): "ας",  ("gen", "pl"): "ων",
    ("dat", "sg"): "ᾳ",   ("dat", "pl"): "αις",
    ("acc", "sg"): "αν",  ("acc", "pl"): "ας",
    ("voc", "sg"): "α",   ("voc", "pl"): "αι",
}

# 1st decl mixed (θάλαττα type: α nom/acc/voc sg, η gen/dat sg) — skip for now

CASE_NAMES = {
    "nom": "nominative", "gen": "genitive", "dat": "dative",
    "acc": "accusative", "voc": "vocative",
}
NUMBER_NAMES = {"sg": "singular", "pl": "plural"}
CASES = list(CASE_NAMES)
NUMBERS = ["sg", "pl"]


@dataclass
class NounInfo:
    word: GreekWord
    nom_sg: str
    stem: str
    declension: str   # "2m", "2n", "1h", "1a"


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


def _parse_noun(word: GreekWord) -> NounInfo | None:
    """Parse the Greek dictionary form 'ἄνθρωπος, -ου' → NounInfo."""
    parts = [p.strip() for p in word.word.split(",", 1)]
    nom = parts[0]
    if len(parts) < 2:
        return None
    gen_part = parts[1].strip()
    if not gen_part.startswith("-"):
        return None
    gen_ending = gen_part[1:]          # e.g. "ου", "ης", "ης", "ας"
    gen_norm = _norm(gen_ending)       # accent-stripped

    nom_norm = _norm(nom)

    if gen_norm == "ου":               # genitive -ου → 2nd declension
        if nom_norm.endswith("ον"):    # neuter -ον
            return NounInfo(word=word, nom_sg=nom, stem=nom[:-2], declension="2n")
        elif nom_norm.endswith("ος"):  # masculine -ος
            return NounInfo(word=word, nom_sg=nom, stem=nom[:-2], declension="2m")

    elif gen_norm in ("ης",):          # genitive -ης → 1st decl η-type
        if nom_norm.endswith("η") or nom[-1] in "ήη":
            return NounInfo(word=word, nom_sg=nom, stem=nom[:-1], declension="1h")

    elif gen_norm in ("ας",):          # genitive -ας → 1st decl α-type
        if nom[-1] in "αά":
            return NounInfo(word=word, nom_sg=nom, stem=nom[:-1], declension="1a")

    return None


def _decline(info: NounInfo, case: str, number: str) -> str | None:
    key = (case, number)
    tables = {"2m": DECL2M, "2n": DECL2N, "1h": DECL1H, "1a": DECL1A}
    table = tables.get(info.declension)
    if table is None:
        return None
    ending = table.get(key)
    return info.stem + ending if ending is not None else None


def load_nouns(max_lesson: int, variant: str = "grc") -> list[NounInfo]:
    words = load_lessons_up_to(max_lesson, variant)
    nouns = []
    for w in words:
        if w.category != "nouns":
            continue
        info = _parse_noun(w)
        if info is not None:
            nouns.append(info)
    return nouns


def generate_exercises(
    max_lesson: int = 2,
    count: int = 10,
    variant: str = "grc",
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
        exercises.append(
            DeclensionExercise(
                id=f"grc-decl-{i}-{_norm(noun.nom_sg)}-{case}-{number}",
                dict_form=noun.word.word,
                definition=noun.word.definition,
                case=case,
                number=number,
                prompt=(
                    f"Give the {CASE_NAMES[case]} {NUMBER_NAMES[number]} of: "
                    f"{noun.word.word} ({noun.word.definition})"
                ),
                answer=form,
                lesson=noun.word.lesson,
            )
        )
    return exercises


def grade_exercise(submitted: str, expected: str) -> tuple[bool, str]:
    correct = _norm(submitted) == _norm(expected)
    if correct:
        return True, f"Correct! The form is {expected}."
    return False, f"Not quite. The expected form is {expected}."
