"""King James Version (KJV) NT translation service.

Source: scrollmapper/bible_databases (public domain)
Run data/nt_greek/prepare_gnt.py to fetch kjv_nt.json.

Format: {book_abbrev: {chapter: {verse: text}}}
where book_abbrev matches GNT abbreviations (Mat, Mrk, ..., Rev).
"""

import json
from pathlib import Path

_BASE = Path(__file__).parents[3] / "data" / "nt_greek"
_KJV_FILE = _BASE / "kjv_nt.json"


class KJVIndex:
    def __init__(self):
        # {abbrev: {chapter: {verse: text}}}
        self._index: dict[str, dict[int, dict[int, str]]] = {}
        self._load()

    def _load(self) -> None:
        if not _KJV_FILE.exists():
            return
        with open(_KJV_FILE, encoding="utf-8") as f:
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


_INDEX: KJVIndex | None = None


def get_index() -> KJVIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = KJVIndex()
    return _INDEX


def get_chapter(book: str, chapter: int) -> dict[int, str]:
    return get_index().get_chapter(book, chapter)


def get_verse(book: str, chapter: int, verse: int) -> str | None:
    return get_index().get_verse(book, chapter, verse)
