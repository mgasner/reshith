"""
Sanskrit noun declension exercise generator.

Supports:
  a-stem masculine (naraḥ, -asya)

Uses IAST transliteration. Grading is diacritic-insensitive.
"""

import random
import unicodedata
from dataclasses import dataclass

from reshith.exercises.sanskrit.vocabulary import SanskritWord, load_lessons_up_to


def _norm(text: str) -> str:
    """Strip diacritics and lowercase — for comparison."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    ).lower().strip()


# ── Paradigm tables (IAST, appended to consonant stem) ────────────────────────

# a-stem masculine: stem = nom_sg[:-2] (strip "aḥ", i.e. strip final 'a' + visarga)
ASTEM_M = {
    ("nom", "sg"): "aḥ",
    ("voc", "sg"): "a",
    ("acc", "sg"): "am",
    ("ins", "sg"): "eṇa",
    ("dat", "sg"): "āya",
    ("abl", "sg"): "āt",
    ("gen", "sg"): "asya",
    ("loc", "sg"): "e",
    ("nom", "pl"): "āḥ",
    ("voc", "pl"): "āḥ",
    ("acc", "pl"): "ān",
    ("ins", "pl"): "aiḥ",
    ("dat", "pl"): "ebhyaḥ",
    ("abl", "pl"): "ebhyaḥ",
    ("gen", "pl"): "āṇām",
    ("loc", "pl"): "eṣu",
}

CASE_NAMES = {
    "nom": "nominative", "voc": "vocative", "acc": "accusative",
    "ins": "instrumental", "dat": "dative", "abl": "ablative",
    "gen": "genitive", "loc": "locative",
}
NUMBER_NAMES = {"sg": "singular", "pl": "plural"}
CASES = list(CASE_NAMES)
NUMBERS = ["sg", "pl"]


@dataclass
class NounInfo:
    word: SanskritWord
    nom_sg: str
    stem: str
    declension: str   # "astem_m"


@dataclass
class DeclensionExercise:
    id: str
    dict_form: str
    devanagari: str
    definition: str
    case: str
    number: str
    prompt: str
    answer: str
    lesson: int


def _parse_noun(word: SanskritWord) -> NounInfo | None:
    """Parse 'naraḥ, -asya' → NounInfo."""
    parts = [p.strip() for p in word.word.split(",", 1)]
    nom = parts[0]
    if len(parts) < 2:
        return None
    gen_part = parts[1].strip()
    if not gen_part.startswith("-"):
        return None
    gen_suffix = gen_part[1:]
    gen_norm = _norm(gen_suffix)
    nom_norm = _norm(nom)

    if gen_norm == "asya" and nom_norm.endswith("ah"):
        # a-stem masculine: nom sg ends in -aḥ (norm: "ah")
        # ḥ (U+1E25) is 1 Unicode codepoint; 'a' before it = 1 codepoint
        # strip "aḥ" = strip last 2 codepoints
        stem = nom[:-2]
        return NounInfo(word=word, nom_sg=nom, stem=stem, declension="astem_m")

    return None


def _decline(info: NounInfo, case: str, number: str) -> str | None:
    key = (case, number)
    tables = {"astem_m": ASTEM_M}
    table = tables.get(info.declension)
    if table is None:
        return None
    ending = table.get(key)
    return info.stem + ending if ending is not None else None


def load_nouns(max_lesson: int) -> list[NounInfo]:
    words = load_lessons_up_to(max_lesson)
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
) -> list[DeclensionExercise]:
    nouns = load_nouns(max_lesson)
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
                id=f"san-decl-{i}-{_norm(noun.nom_sg)}-{case}-{number}",
                dict_form=noun.word.word,
                devanagari=noun.word.devanagari,
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
