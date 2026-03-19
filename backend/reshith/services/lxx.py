"""Septuagint (LXX) interlinear service.

Data source:
  STEPBible TALXX — Translators Amalgamated LXX (CC BY 4.0)
  https://github.com/tyndale/STEPBible-Data
  Run data/nt_greek/prepare_lxx.py to fetch the data file.

Covers the complete Septuagint including deuterocanonical books.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parents[3] / "data" / "nt_greek"
TALXX_FILE = DATA_DIR / "TALXX.txt"

# TALXX.txt column layout (tab-separated, produced by prepare_lxx.py):
# [0] ref     e.g. "Gen.1.1#01=T"
# [1] greek   e.g. "ἐν"
# [2] (empty)
# [3] (empty)
# [4] (empty)
# [5] grammar e.g. "P---------"  (CATSS morphology code)
# [6] (empty)
# [7] (empty)
# [8] lemma   e.g. "ἐν"  (stored in 'expanded' field)

LXX_BOOK_ORDER = [
    "Gen", "Exo", "Lev", "Num", "Deu",
    "Jos", "Jdg", "Rut", "1Sa", "2Sa", "1Ki", "2Ki",
    "1Ch", "2Ch", "Ezr", "Neh", "Est",
    "Tob", "Jdt", "1Ma", "2Ma", "3Ma", "4Ma",
    "Psa", "Pro", "Ecc", "Sng", "Job", "Wis", "Sir",
    "Isa", "Jer", "Lam", "Bar", "Ezk", "Dan",
    "Hos", "Jol", "Amo", "Oba", "Jon", "Mic",
    "Nah", "Hab", "Zep", "Hag", "Zec", "Mal",
]

LXX_BOOK_NAMES: dict[str, str] = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus",
    "Num": "Numbers", "Deu": "Deuteronomy", "Jos": "Joshua",
    "Jdg": "Judges", "Rut": "Ruth", "1Sa": "1 Samuel",
    "2Sa": "2 Samuel", "1Ki": "1 Kings", "2Ki": "2 Kings",
    "1Ch": "1 Chronicles", "2Ch": "2 Chronicles",
    "Ezr": "Ezra", "Neh": "Nehemiah", "Est": "Esther",
    "Tob": "Tobit", "Jdt": "Judith",
    "1Ma": "1 Maccabees", "2Ma": "2 Maccabees",
    "3Ma": "3 Maccabees", "4Ma": "4 Maccabees",
    "Psa": "Psalms", "Pro": "Proverbs", "Ecc": "Ecclesiastes",
    "Sng": "Song of Songs", "Job": "Job", "Wis": "Wisdom", "Sir": "Sirach",
    "Isa": "Isaiah", "Jer": "Jeremiah", "Lam": "Lamentations",
    "Bar": "Baruch", "Ezk": "Ezekiel", "Dan": "Daniel",
    "Hos": "Hosea", "Jol": "Joel", "Amo": "Amos", "Oba": "Obadiah",
    "Jon": "Jonah", "Mic": "Micah", "Nah": "Nahum",
    "Hab": "Habakkuk", "Zep": "Zephaniah", "Hag": "Haggai",
    "Zec": "Zechariah", "Mal": "Malachi",
}

REF_RE = re.compile(r'^([A-Z1-9][a-zA-Z0-9]+)\.(\d+)\.(\d+)#(\d+)=([A-Za-z])')


@dataclass
class LXXWord:
    ref: str
    book: str
    chapter: int
    verse: int
    token: int
    text_type: str
    greek: str
    transliteration: str
    translation: str
    dstrongs: str
    grammar: str
    expanded: str


@dataclass
class LXXIndex:
    data: dict[str, dict[int, dict[int, list[LXXWord]]]] = field(default_factory=dict)
    book_chapters: dict[str, int] = field(default_factory=dict)
    chapter_verses: dict[str, dict[int, int]] = field(default_factory=dict)
    loaded: bool = False


_INDEX: LXXIndex | None = None


def _parse_file() -> LXXIndex:
    idx = LXXIndex()

    if not TALXX_FILE.exists():
        idx.loaded = True
        return idx

    with open(TALXX_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line or line.startswith("\t") or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 2:
                continue

            ref = parts[0].strip()
            m = REF_RE.match(ref)
            if not m:
                continue

            book = m.group(1)
            chapter = int(m.group(2))
            verse = int(m.group(3))
            token = int(m.group(4))
            text_type = m.group(5)

            word = LXXWord(
                ref=ref,
                book=book,
                chapter=chapter,
                verse=verse,
                token=token,
                text_type=text_type,
                greek=parts[1].strip() if len(parts) > 1 else "",
                transliteration=parts[2].strip() if len(parts) > 2 else "",
                translation=parts[3].strip() if len(parts) > 3 else "",
                dstrongs=parts[4].strip() if len(parts) > 4 else "",
                grammar=parts[5].strip() if len(parts) > 5 else "",
                expanded=parts[8].strip() if len(parts) > 8 else "",
            )

            if book not in idx.data:
                idx.data[book] = {}
                idx.book_chapters[book] = 0
                idx.chapter_verses[book] = {}

            if chapter not in idx.data[book]:
                idx.data[book][chapter] = {}

            if verse not in idx.data[book][chapter]:
                idx.data[book][chapter][verse] = []

            idx.data[book][chapter][verse].append(word)

            if chapter > idx.book_chapters[book]:
                idx.book_chapters[book] = chapter

            if chapter not in idx.chapter_verses[book]:
                idx.chapter_verses[book][chapter] = 0
            if verse > idx.chapter_verses[book][chapter]:
                idx.chapter_verses[book][chapter] = verse

    idx.loaded = True
    return idx


def get_index() -> LXXIndex:
    global _INDEX
    if _INDEX is None or not _INDEX.loaded:
        _INDEX = _parse_file()
    return _INDEX


def get_books() -> list[dict]:
    idx = get_index()
    return [
        {"abbrev": b, "name": LXX_BOOK_NAMES.get(b, b), "chapters": idx.book_chapters[b]}
        for b in LXX_BOOK_ORDER
        if b in idx.book_chapters
    ]


def get_chapter_verse_counts(book: str) -> dict[int, int]:
    idx = get_index()
    return dict(idx.chapter_verses.get(book, {}))


def get_verse(book: str, chapter: int, verse: int) -> list[LXXWord]:
    idx = get_index()
    return list(idx.data.get(book, {}).get(chapter, {}).get(verse, []))


def get_chapter(book: str, chapter: int) -> dict[int, list[LXXWord]]:
    idx = get_index()
    return dict(idx.data.get(book, {}).get(chapter, {}))


def search(query: str, limit: int = 50) -> list[LXXWord]:
    idx = get_index()
    q = query.strip().lower()
    if not q:
        return []
    results: list[LXXWord] = []
    for book in LXX_BOOK_ORDER:
        if book not in idx.data:
            continue
        for ch_data in idx.data[book].values():
            for v_words in ch_data.values():
                for w in v_words:
                    if (
                        q in w.greek.lower()
                        or q in w.transliteration.lower()
                        or q in w.translation.lower()
                        or q in w.dstrongs.lower()
                    ):
                        results.append(w)
                        if len(results) >= limit:
                            return results
    return results
