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
TAGNT_FILE = DATA_DIR / "TAGNT.txt"

GNT_BOOK_ORDER = [
    "Mat", "Mrk", "Luk", "Jhn", "Act",
    "Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col",
    "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm",
    "Heb", "Jas", "1Pe", "2Pe", "1Jn", "2Jn", "3Jn", "Jud", "Rev",
]

GNT_BOOK_NAMES: dict[str, str] = {
    "Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John",
    "Act": "Acts", "Rom": "Romans", "1Co": "1 Corinthians", "2Co": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Php": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jn": "1 John",
    "2Jn": "2 John", "3Jn": "3 John", "Jud": "Jude", "Rev": "Revelation",
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

    if not TAGNT_FILE.exists():
        idx.loaded = True
        return idx

    with open(TAGNT_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line or line.startswith("\t") or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 4:
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

            # TAGNT column layout:
            # [0] ref          e.g. "Mat.1.1#01=NKO"
            # [1] greek+trans  e.g. "Βίβλος (Biblos)"
            # [2] gloss        e.g. "[The] book"
            # [3] dStrongs=grammar  e.g. "G0976=N-NSF"
            # [4] lemma=gloss  e.g. "βίβλος=book"
            greek_raw = parts[1].strip() if len(parts) > 1 else ""
            paren_idx = greek_raw.find(" (")
            if paren_idx >= 0:
                greek = greek_raw[:paren_idx]
                transliteration = greek_raw[paren_idx + 2:].rstrip(")")
            else:
                greek = greek_raw
                transliteration = ""

            translation = parts[2].strip() if len(parts) > 2 else ""

            ds_gram = parts[3].strip() if len(parts) > 3 else ""
            if "=" in ds_gram:
                dstrongs, grammar = ds_gram.split("=", 1)
            else:
                dstrongs, grammar = ds_gram, ""

            expanded = parts[4].strip() if len(parts) > 4 else ""

            word = GNTWord(
                ref=ref,
                book=book,
                chapter=chapter,
                verse=verse,
                token=token,
                text_type=text_type,
                greek=greek,
                transliteration=transliteration,
                translation=translation,
                dstrongs=dstrongs,
                grammar=grammar,
                expanded=expanded,
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
