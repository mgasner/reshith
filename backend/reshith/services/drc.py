"""Douay-Rheims Challoner (DRC) verse translation service.

Source: scrollmapper/bible_databases DRC.json (public domain).
Covers all 73 canonical Catholic books.
"""

import json
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent.parent / "data" / "vulgate"
_DRC_FILE = _BASE / "drc.json"

# Map DRC book names → our abbreviations
_DRC_NAME_TO_ABBREV: dict[str, str] = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV",
    "Numbers": "NUM", "Deuteronomy": "DEU", "Joshua": "JOS",
    "Judges": "JDG", "Ruth": "RUT", "I Samuel": "1SAM",
    "II Samuel": "2SAM", "I Kings": "1KGS", "II Kings": "2KGS",
    "I Chronicles": "1CHR", "II Chronicles": "2CHR",
    "Ezra": "EZR", "Nehemiah": "NEH", "Tobit": "TOB",
    "Judith": "JDT", "Esther": "EST", "Job": "JOB",
    "Psalms": "PSA", "Proverbs": "PRO", "Ecclesiastes": "ECC",
    "Song of Solomon": "SNG", "Wisdom": "WIS", "Sirach": "SIR",
    "Isaiah": "ISA", "Jeremiah": "JER", "Lamentations": "LAM",
    "Baruch": "BAR", "Ezekiel": "EZK", "Daniel": "DAN",
    "Hosea": "HOS", "Joel": "JOL", "Amos": "AMO",
    "Obadiah": "OBA", "Jonah": "JON", "Micah": "MIC",
    "Nahum": "NAH", "Habakkuk": "HAB", "Zephaniah": "ZEP",
    "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL",
    "I Maccabees": "1MAC", "II Maccabees": "2MAC",
    "Matthew": "MATT", "Mark": "MARK", "Luke": "LUKE",
    "John": "JOHN", "Acts": "ACTS", "Romans": "ROM",
    "I Corinthians": "1COR", "II Corinthians": "2COR",
    "Galatians": "GAL", "Ephesians": "EPH", "Philippians": "PHIL",
    "Colossians": "COL", "I Thessalonians": "1THESS",
    "II Thessalonians": "2THESS", "I Timothy": "1TIM",
    "II Timothy": "2TIM", "Titus": "TIT", "Philemon": "PHILEM",
    "Hebrews": "HEB", "James": "JAS", "I Peter": "1PET",
    "II Peter": "2PET", "I John": "1JOHN", "II John": "2JOHN",
    "III John": "3JOHN", "Jude": "JUDE", "Revelation of John": "REV",
}


class DrcIndex:
    def __init__(self):
        # {abbrev: {chapter: {verse: text}}}
        self._index: dict[str, dict[int, dict[int, str]]] = {}
        self._load()

    def _load(self) -> None:
        if not _DRC_FILE.exists():
            return
        with open(_DRC_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for book in data["books"]:
            abbrev = _DRC_NAME_TO_ABBREV.get(book["name"])
            if abbrev is None:
                continue
            book_idx: dict[int, dict[int, str]] = {}
            for ch_obj in book["chapters"]:
                ch = ch_obj["chapter"]
                verse_idx: dict[int, str] = {}
                for v_obj in ch_obj["verses"]:
                    verse_idx[v_obj["verse"]] = v_obj["text"]
                book_idx[ch] = verse_idx
            self._index[abbrev] = book_idx

    def get_verse(self, book: str, chapter: int, verse: int) -> str | None:
        return self._index.get(book, {}).get(chapter, {}).get(verse)

    def get_chapter(self, book: str, chapter: int) -> dict[int, str]:
        """Returns {verse_num: text} for the given chapter."""
        return self._index.get(book, {}).get(chapter, {})


_INDEX: DrcIndex | None = None


def get_index() -> DrcIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = DrcIndex()
    return _INDEX


def get_verse(book: str, chapter: int, verse: int) -> str | None:
    return get_index().get_verse(book, chapter, verse)


def get_chapter(book: str, chapter: int) -> dict[int, str]:
    return get_index().get_chapter(book, chapter)
