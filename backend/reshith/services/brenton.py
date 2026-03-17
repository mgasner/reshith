"""Brenton LXX English translation service.

Source: Lancelot Brenton, 1851 (public domain)
Run data/nt_greek/prepare_lxx.py to fetch brenton_lxx.json.

Format: {book_abbrev: {chapter: {verse: text}}}
where book_abbrev matches LXX abbreviations (Gen, Exo, ..., Mal).
"""

import json
from pathlib import Path

_BASE = Path(__file__).parents[3] / "data" / "nt_greek"
_BRENTON_FILE = _BASE / "brenton_lxx.json"


class BrentonIndex:
    def __init__(self):
        # {abbrev: {chapter: {verse: text}}}
        self._index: dict[str, dict[int, dict[int, str]]] = {}
        self._load()

    def _load(self) -> None:
        if not _BRENTON_FILE.exists():
            return
        with open(_BRENTON_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # Format: {abbrev: {"1": {"1": "text", ...}, ...}, ...}
        for book, chapters in data.items():
            book_idx: dict[int, dict[int, str]] = {}
            for ch_str, verses in chapters.items():
                verse_idx: dict[int, str] = {}
                for v_str, text in verses.items():
                    verse_idx[int(v_str)] = text
                book_idx[int(ch_str)] = verse_idx
            self._index[book] = book_idx

    def get_chapter(self, book: str, chapter: int) -> dict[int, str]:
        return self._index.get(book, {}).get(chapter, {})

    def get_verse(self, book: str, chapter: int, verse: int) -> str | None:
        return self._index.get(book, {}).get(chapter, {}).get(verse)


_INDEX: BrentonIndex | None = None


def get_index() -> BrentonIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = BrentonIndex()
    return _INDEX


def get_chapter(book: str, chapter: int) -> dict[int, str]:
    return get_index().get_chapter(book, chapter)


def get_verse(book: str, chapter: int, verse: int) -> str | None:
    return get_index().get_verse(book, chapter, verse)
