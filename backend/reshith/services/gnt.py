"""Greek New Testament (GNT) interlinear service.

Data source:
  STEPBible TANTT — Translators Amalgamated NT Text (CC BY 4.0)
  https://github.com/tyndale/STEPBible-Data
  Run data/nt_greek/prepare_gnt.py to fetch the data file.

Covers all 27 NT books in the same format as TAHOT.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parents[3] / "data" / "nt_greek"
TANTT_FILE = DATA_DIR / "TANTT.txt"

GNT_BOOK_ORDER = [
    "Mat", "Mrk", "Lke", "Jhn", "Act",
    "Rom", "1Co", "2Co", "Gal", "Eph", "Phl", "Col",
    "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm",
    "Hbr", "Jas", "1Pe", "2Pe", "1Jn", "2Jn", "3Jn", "Jde", "Rev",
]

GNT_BOOK_NAMES: dict[str, str] = {
    "Mat": "Matthew", "Mrk": "Mark", "Lke": "Luke", "Jhn": "John",
    "Act": "Acts", "Rom": "Romans", "1Co": "1 Corinthians", "2Co": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Phl": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Hbr": "Hebrews",
    "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jn": "1 John",
    "2Jn": "2 John", "3Jn": "3 John", "Jde": "Jude", "Rev": "Revelation",
}

_BOOK_ORDER_MAP: dict[str, int] = {b: i for i, b in enumerate(GNT_BOOK_ORDER)}

REF_RE = re.compile(r'^([A-Z1-9][a-zA-Z0-9]+)\.(\d+)\.(\d+)#(\d+)=([A-Za-z])')


@dataclass
class GNTWord:
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
class GNTIndex:
    # book -> chapter -> verse -> [words]
    data: dict[str, dict[int, dict[int, list[GNTWord]]]] = field(default_factory=dict)
    book_chapters: dict[str, int] = field(default_factory=dict)
    chapter_verses: dict[str, dict[int, int]] = field(default_factory=dict)
    loaded: bool = False


_INDEX: GNTIndex | None = None


def _parse_file() -> GNTIndex:
    idx = GNTIndex()

    if not TANTT_FILE.exists():
        idx.loaded = True
        return idx

    past_header = False
    with open(TANTT_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line or line.startswith("\t") or line.startswith("#"):
                continue
            # STEPBible header ends with a line starting with "Eng"
            if line.startswith("Eng"):
                past_header = True
                continue
            if not past_header:
                continue

            parts = line.split("\t")
            if len(parts) < 6:
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

            word = GNTWord(
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


def get_index() -> GNTIndex:
    global _INDEX
    if _INDEX is None or not _INDEX.loaded:
        _INDEX = _parse_file()
    return _INDEX


def get_books() -> list[dict]:
    idx = get_index()
    return [
        {"abbrev": b, "name": GNT_BOOK_NAMES.get(b, b), "chapters": idx.book_chapters[b]}
        for b in GNT_BOOK_ORDER
        if b in idx.book_chapters
    ]


def get_chapter_verse_counts(book: str) -> dict[int, int]:
    idx = get_index()
    return dict(idx.chapter_verses.get(book, {}))


def get_verse(book: str, chapter: int, verse: int) -> list[GNTWord]:
    idx = get_index()
    return list(idx.data.get(book, {}).get(chapter, {}).get(verse, []))


def get_chapter(book: str, chapter: int) -> dict[int, list[GNTWord]]:
    idx = get_index()
    return dict(idx.data.get(book, {}).get(chapter, {}))


def search(query: str, limit: int = 50) -> list[GNTWord]:
    idx = get_index()
    q = query.strip().lower()
    if not q:
        return []
    results: list[GNTWord] = []
    for book in GNT_BOOK_ORDER:
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
