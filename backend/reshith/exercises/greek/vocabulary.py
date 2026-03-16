"""Load Greek vocabulary from lesson JSON files."""

import json
from dataclasses import dataclass
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent.parent.parent / "data"


def _data_dir(variant: str) -> Path:
    """Return the data directory for a Greek variant ('grc' or 'gnt')."""
    return _BASE / ("greek" if variant == "grc" else "nt_greek")


@dataclass
class GreekWord:
    word: str           # dictionary form, e.g. "ἄνθρωπος, -ου"
    transliteration: str  # grammatical label
    definition: str
    category: str
    lesson: int


def load_lesson(lesson_num: int, variant: str = "grc") -> list[GreekWord]:
    path = _data_dir(variant) / f"lesson{lesson_num:02d}.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        GreekWord(
            word=card["word"],
            transliteration=card.get("transliteration", ""),
            definition=card["definition"],
            category=card["category"],
            lesson=lesson_num,
        )
        for card in data.get("cards", [])
    ]


def load_lessons_up_to(max_lesson: int, variant: str = "grc") -> list[GreekWord]:
    words: list[GreekWord] = []
    for n in range(1, max_lesson + 1):
        try:
            words.extend(load_lesson(n, variant))
        except FileNotFoundError:
            break
    return words
