"""Jewish Publication Society 1917 translation service.

Source: scrollmapper/bible_databases JPS.json (public domain).
Covers all 39 books of the Hebrew canon (Torah, Prophets, Writings).
"""

import json
from pathlib import Path

_FILE = Path(__file__).parent.parent.parent.parent / "data" / "hebrew" / "jps1917.json"

# JPS book name → TAHOT abbreviation
_NAME_TO_ABBREV: dict[str, str] = {
    "Genesis": "Gen",
    "Exodus": "Exo",
    "Leviticus": "Lev",
    "Numbers": "Num",
    "Deuteronomy": "Deu",
    "Joshua": "Jos",
    "Judges": "Jdg",
    "Ruth": "Rut",
    "I Samuel": "1Sa",
    "II Samuel": "2Sa",
    "I Kings": "1Ki",
    "II Kings": "2Ki",
    "I Chronicles": "1Ch",
    "II Chronicles": "2Ch",
    "Ezra": "Ezr",
    "Nehemiah": "Neh",
    "Esther": "Est",
    "Job": "Job",
    "Psalms": "Psa",
    "Proverbs": "Pro",
    "Ecclesiastes": "Ecc",
    "Song of Solomon": "Sng",
    "Isaiah": "Isa",
    "Jeremiah": "Jer",
    "Lamentations": "Lam",
    "Ezekiel": "Ezk",
    "Daniel": "Dan",
    "Hosea": "Hos",
    "Joel": "Jol",
    "Amos": "Amo",
    "Obadiah": "Oba",
    "Jonah": "Jon",
    "Micah": "Mic",
    "Nahum": "Nam",
    "Habakkuk": "Hab",
    "Zephaniah": "Zep",
    "Haggai": "Hag",
    "Zechariah": "Zec",
    "Malachi": "Mal",
}


class JpsIndex:
    def __init__(self) -> None:
        # {tahot_abbrev: {chapter: {verse: text}}}
        self._index: dict[str, dict[int, dict[int, str]]] = {}
        self._load()

    def _load(self) -> None:
        if not _FILE.exists():
            return
        with open(_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for book in data["books"]:
            abbrev = _NAME_TO_ABBREV.get(book["name"])
            if abbrev is None:
                continue
            book_idx: dict[int, dict[int, str]] = {}
            for ch_obj in book["chapters"]:
                ch = ch_obj["chapter"]
                book_idx[ch] = {v["verse"]: v["text"].strip() for v in ch_obj["verses"]}
            self._index[abbrev] = book_idx

    def get_verse(self, book: str, chapter: int, verse: int) -> str | None:
        return self._index.get(book, {}).get(chapter, {}).get(verse)

    def get_chapter(self, book: str, chapter: int) -> dict[int, str]:
        """Returns {verse_num: text} for the given chapter."""
        return self._index.get(book, {}).get(chapter, {})


_INDEX: JpsIndex | None = None


def get_index() -> JpsIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = JpsIndex()
    return _INDEX


def get_verse(book: str, chapter: int, verse: int) -> str | None:
    return get_index().get_verse(book, chapter, verse)


def get_chapter(book: str, chapter: int) -> dict[int, str]:
    return get_index().get_chapter(book, chapter)
