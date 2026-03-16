"""Vulgate Latin interlinear service.

Data sources:
  NT — PROIEL treebank (CC BY-NC-SA 4.0), human-reviewed
       https://github.com/proiel/proiel-treebank
  OT — Clementine Vulgate (MIT) tagged with Stanza Latin/PROIEL (~88-93% accuracy)
       https://github.com/scrollmapper/bible_databases

Covers all 73 books (46 OT + 27 NT).
"""

import csv
from dataclasses import dataclass
from pathlib import Path

_BASE = Path(__file__).parent.parent.parent.parent / "data" / "vulgate"
_NT_FILE = _BASE / "nt_tokens.tsv"
_OT_FILE = _BASE / "ot_tokens.tsv"

# Canonical book order for navigation (OT then NT)
BOOK_ORDER = [
    # OT
    "GEN", "EXO", "LEV", "NUM", "DEU",
    "JOS", "JDG", "RUT", "1SAM", "2SAM", "1KGS", "2KGS",
    "1CHR", "2CHR", "EZR", "NEH", "TOB", "JDT", "EST",
    "1MAC", "2MAC", "JOB", "PSA", "PRO", "ECC", "SNG",
    "WIS", "SIR", "ISA", "JER", "LAM", "BAR", "EZK", "DAN",
    "HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAH",
    "HAB", "ZEP", "HAG", "ZEC", "MAL",
    # NT
    "MATT", "MARK", "LUKE", "JOHN", "ACTS",
    "ROM", "1COR", "2COR", "GAL", "EPH", "PHIL", "COL",
    "1THESS", "2THESS", "1TIM", "2TIM", "TIT", "PHILEM",
    "HEB", "JAS", "1PET", "2PET", "1JOHN", "2JOHN", "3JOHN", "JUDE", "REV",
]

BOOK_NAMES = {
    # OT
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus",
    "NUM": "Numbers", "DEU": "Deuteronomy", "JOS": "Joshua",
    "JDG": "Judges", "RUT": "Ruth", "1SAM": "1 Samuel",
    "2SAM": "2 Samuel", "1KGS": "1 Kings", "2KGS": "2 Kings",
    "1CHR": "1 Chronicles", "2CHR": "2 Chronicles",
    "EZR": "Ezra", "NEH": "Nehemiah", "TOB": "Tobit",
    "JDT": "Judith", "EST": "Esther", "1MAC": "1 Maccabees",
    "2MAC": "2 Maccabees", "JOB": "Job", "PSA": "Psalms",
    "PRO": "Proverbs", "ECC": "Ecclesiastes", "SNG": "Song of Songs",
    "WIS": "Wisdom", "SIR": "Sirach", "ISA": "Isaiah",
    "JER": "Jeremiah", "LAM": "Lamentations", "BAR": "Baruch",
    "EZK": "Ezekiel", "DAN": "Daniel", "HOS": "Hosea",
    "JOL": "Joel", "AMO": "Amos", "OBA": "Obadiah",
    "JON": "Jonah", "MIC": "Micah", "NAH": "Nahum",
    "HAB": "Habakkuk", "ZEP": "Zephaniah", "HAG": "Haggai",
    "ZEC": "Zechariah", "MAL": "Malachi",
    # NT
    "MATT": "Matthew", "MARK": "Mark", "LUKE": "Luke", "JOHN": "John",
    "ACTS": "Acts", "ROM": "Romans", "1COR": "1 Corinthians", "2COR": "2 Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHIL": "Philippians", "COL": "Colossians",
    "1THESS": "1 Thessalonians", "2THESS": "2 Thessalonians",
    "1TIM": "1 Timothy", "2TIM": "2 Timothy", "TIT": "Titus", "PHILEM": "Philemon",
    "HEB": "Hebrews", "JAS": "James", "1PET": "1 Peter", "2PET": "2 Peter",
    "1JOHN": "1 John", "2JOHN": "2 John", "3JOHN": "3 John", "JUDE": "Jude",
    "REV": "Revelation",
}


@dataclass
class VulgateToken:
    ref: str          # e.g. "MATT.1.1#01"
    book: str         # e.g. "MATT"
    chapter: int
    verse: int
    token: int
    form: str         # surface Latin word
    lemma: str        # dictionary headword
    pos: str          # 2-char PROIEL POS code
    morphology: str   # 10-char PROIEL morphology
    relation: str     # dependency relation


class VulgateIndex:
    def __init__(self):
        self._index: dict[str, dict[int, dict[int, list[VulgateToken]]]] = {}
        self._book_chapters: dict[str, set] = {}
        self._chapter_verses: dict[tuple, set] = {}
        self._load()

    def _load_file(self, path: Path) -> None:
        if not path.exists():
            return
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                book = row["book"]
                chapter = int(row["chapter"])
                verse = int(row["verse"])
                token = VulgateToken(
                    ref=row["ref"],
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    token=int(row["token"]),
                    form=row["form"],
                    lemma=row["lemma"],
                    pos=row["pos"],
                    morphology=row["morphology"],
                    relation=row["relation"],
                )
                self._index.setdefault(book, {}).setdefault(chapter, {}).setdefault(verse, []).append(token)
                self._book_chapters.setdefault(book, set()).add(chapter)
                self._chapter_verses.setdefault((book, chapter), set()).add(verse)

    def _load(self) -> None:
        self._load_file(_OT_FILE)
        self._load_file(_NT_FILE)

    def get_books(self) -> list[dict]:
        result = []
        for abbrev in BOOK_ORDER:
            if abbrev in self._book_chapters:
                result.append({
                    "abbrev": abbrev,
                    "name": BOOK_NAMES.get(abbrev, abbrev),
                    "chapters": max(self._book_chapters[abbrev]),
                })
        return result

    def get_chapter_verse_counts(self, book: str) -> dict[int, int]:
        result = {}
        for ch in sorted(self._book_chapters.get(book, [])):
            verses = self._chapter_verses.get((book, ch), set())
            result[ch] = max(verses) if verses else 0
        return result

    def get_verse(self, book: str, chapter: int, verse: int) -> list[VulgateToken]:
        return self._index.get(book, {}).get(chapter, {}).get(verse, [])

    def get_chapter(self, book: str, chapter: int) -> dict[int, list[VulgateToken]]:
        return self._index.get(book, {}).get(chapter, {})

    def search(self, query: str, limit: int = 50) -> list[VulgateToken]:
        query_lower = query.lower()
        results = []
        for book in BOOK_ORDER:
            if book not in self._index:
                continue
            for ch in sorted(self._index[book]):
                for v in sorted(self._index[book][ch]):
                    for tok in self._index[book][ch][v]:
                        if query_lower in tok.form.lower() or query_lower in tok.lemma.lower():
                            results.append(tok)
                            if len(results) >= limit:
                                return results
        return results


_INDEX: VulgateIndex | None = None


def get_index() -> VulgateIndex:
    global _INDEX
    if _INDEX is None:
        _INDEX = VulgateIndex()
    return _INDEX


def get_books() -> list[dict]:
    return get_index().get_books()


def get_chapter_verse_counts(book: str) -> dict[int, int]:
    return get_index().get_chapter_verse_counts(book)


def get_verse(book: str, chapter: int, verse: int) -> list[VulgateToken]:
    return get_index().get_verse(book, chapter, verse)


def get_chapter(book: str, chapter: int) -> dict[int, list[VulgateToken]]:
    return get_index().get_chapter(book, chapter)


def search(query: str, limit: int = 50) -> list[VulgateToken]:
    return get_index().search(query, limit)
