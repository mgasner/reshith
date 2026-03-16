"""Load Latin vocabulary from lesson JSON files."""

import json
from dataclasses import dataclass
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent.parent.parent / "data"


def _data_dir(variant: str) -> Path:
    """Return the data directory for a Latin variant ('lat' or 'ecl')."""
    return _BASE / ("latin" if variant == "lat" else "ecclesiastical_latin")


@dataclass
class LatinWord:
    word: str           # dictionary form, e.g. "puella, -ae"
    transliteration: str  # grammatical hint, e.g. "f. girl"
    definition: str
    category: str
    lesson: int


def load_lesson(lesson_num: int, variant: str = "lat") -> list[LatinWord]:
    lesson_path = _data_dir(variant) / f"lesson{lesson_num:02d}.json"
    with open(lesson_path, encoding="utf-8") as f:
        data = json.load(f)
    words = []
    for card in data.get("cards", []):
        words.append(
            LatinWord(
                word=card["word"],
                transliteration=card.get("transliteration", ""),
                definition=card["definition"],
                category=card["category"],
                lesson=lesson_num,
            )
        )
    return words


def load_lessons_up_to(max_lesson: int, variant: str = "lat") -> list[LatinWord]:
    words = []
    for n in range(1, max_lesson + 1):
        try:
            words.extend(load_lesson(n, variant))
        except FileNotFoundError:
            break
    return words
