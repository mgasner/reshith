"""Load Sanskrit vocabulary from lesson JSON files."""

import json
from dataclasses import dataclass
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent.parent.parent / "data"
_DATA_DIR = _BASE / "sanskrit"


@dataclass
class SanskritWord:
    word: str           # IAST dictionary form, e.g. "naraḥ, -asya"
    transliteration: str  # grammatical type label
    definition: str
    category: str
    lesson: int
    devanagari: str = ""


def load_lesson(lesson_num: int) -> list[SanskritWord]:
    path = _DATA_DIR / f"lesson{lesson_num:02d}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        SanskritWord(
            word=card["word"],
            transliteration=card.get("transliteration", ""),
            definition=card["definition"],
            category=card["category"],
            lesson=lesson_num,
            devanagari=card.get("devanagari", ""),
        )
        for card in data.get("cards", [])
    ]


def load_lessons_up_to(max_lesson: int) -> list[SanskritWord]:
    words: list[SanskritWord] = []
    for n in range(1, max_lesson + 1):
        try:
            words.extend(load_lesson(n))
        except FileNotFoundError:
            break
    return words
