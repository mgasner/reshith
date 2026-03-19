"""TAHOT (Translators Amalgamated Hebrew OT) parser and index."""

import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parents[3] / "data" / "hebrew" / "tahot_raw"

TAHOT_FILES = [
    DATA_DIR / "TAHOT_Gen-Deu.txt",
    DATA_DIR / "TAHOT_Jos-Est.txt",
    DATA_DIR / "TAHOT_Job-Sng.txt",
    DATA_DIR / "TAHOT_Isa-Mal.txt",
]

# Canonical OT book order
OT_BOOK_ORDER = [
    "Gen", "Exo", "Lev", "Num", "Deu",
    "Jos", "Jdg", "1Sa", "2Sa", "1Ki", "2Ki",
    "1Ch", "2Ch", "Ezr", "Neh", "Est",
    "Job", "Psa", "Pro", "Ecc", "Sng",
    "Isa", "Jer", "Lam", "Ezk", "Dan",
    "Hos", "Jol", "Amo", "Oba", "Jon",
    "Mic", "Nah", "Hab", "Zep", "Hag", "Zec", "Mal",
]

_BOOK_ORDER_MAP: dict[str, int] = {b: i for i, b in enumerate(OT_BOOK_ORDER)}

REF_RE = re.compile(r'^([A-Z1-9][a-zA-Z0-9]+)\.(\d+)\.(\d+)(?:\([^)]+\))?#(\d+)=([A-Z])')


@dataclass
class TahotWord:
    ref: str
    book: str
    chapter: int
    verse: int
    token: int
    text_type: str       # L, Q, K, R, X
    hebrew: str
    transliteration: str
    translation: str
    dstrongs: str
    grammar: str
    root_strongs: str
    expanded: str


@dataclass
class TahotIndex:
    # book -> chapter -> verse -> [words]
    data: dict[str, dict[int, dict[int, list[TahotWord]]]] = field(default_factory=dict)
    # book -> max chapter
    book_chapters: dict[str, int] = field(default_factory=dict)
    # book -> chapter -> max verse
    chapter_verses: dict[str, dict[int, int]] = field(default_factory=dict)
    loaded: bool = False


_INDEX: TahotIndex | None = None


def _parse_files() -> TahotIndex:
    idx = TahotIndex()

    for filepath in TAHOT_FILES:
        if not filepath.exists():
            continue

        past_header = False
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n")

                if not line or line.startswith("\t") or line.startswith("#"):
                    continue
                if line.startswith("Eng (Heb) Ref"):
                    past_header = True
                    continue
                if not past_header:
                    continue

                parts = line.split("\t")
                if len(parts) < 9:
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

                word = TahotWord(
                    ref=ref,
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    token=token,
                    text_type=text_type,
                    hebrew=parts[1].strip() if len(parts) > 1 else "",
                    transliteration=parts[2].strip() if len(parts) > 2 else "",
                    translation=parts[3].strip() if len(parts) > 3 else "",
                    dstrongs=parts[4].strip() if len(parts) > 4 else "",
                    grammar=parts[5].strip() if len(parts) > 5 else "",
                    root_strongs=parts[8].strip() if len(parts) > 8 else "",
                    expanded=parts[11].strip() if len(parts) > 11 else "",
                )

                # Index
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


def get_index() -> TahotIndex:
    global _INDEX
    if _INDEX is None or not _INDEX.loaded:
        _INDEX = _parse_files()
    return _INDEX


def get_books() -> list[dict]:
    """Return ordered list of books with chapter counts."""
    idx = get_index()
    books = []
    for book in OT_BOOK_ORDER:
        if book in idx.book_chapters:
            books.append({"abbrev": book, "chapters": idx.book_chapters[book]})
    return books


def get_chapter_verse_counts(book: str) -> dict[int, int]:
    """Return {chapter: verse_count} for a book."""
    idx = get_index()
    return dict(idx.chapter_verses.get(book, {}))


def get_verse(book: str, chapter: int, verse: int) -> list[TahotWord]:
    """Return all tokens for a specific verse."""
    idx = get_index()
    return list(idx.data.get(book, {}).get(chapter, {}).get(verse, []))


def get_chapter(book: str, chapter: int) -> dict[int, list[TahotWord]]:
    """Return all verses in a chapter."""
    idx = get_index()
    return dict(idx.data.get(book, {}).get(chapter, {}))


def get_range(
    book: str,
    start_chapter: int,
    start_verse: int,
    end_chapter: int,
    end_verse: int,
) -> dict[tuple[int, int], list[TahotWord]]:
    """Return words for a passage range, keyed by (chapter, verse).

    Inclusive on both ends: get_range("Gen", 1, 1, 3, 4) returns
    Gen 1:1 through Gen 3:4.
    """
    idx = get_index()
    book_data = idx.data.get(book, {})
    result: dict[tuple[int, int], list[TahotWord]] = {}

    for ch in sorted(book_data.keys()):
        if ch < start_chapter or ch > end_chapter:
            continue
        for v in sorted(book_data[ch].keys()):
            if ch == start_chapter and v < start_verse:
                continue
            if ch == end_chapter and v > end_verse:
                continue
            result[(ch, v)] = list(book_data[ch][v])

    return result


def search_words(query: str, limit: int = 50) -> list[TahotWord]:
    """Search across all words by Hebrew, transliteration, translation, or Strong's."""
    idx = get_index()
    q = query.strip().lower()
    if not q:
        return []

    results: list[TahotWord] = []

    for book_data in idx.data.values():
        for chapter_data in book_data.values():
            for verse_words in chapter_data.values():
                for word in verse_words:
                    if (
                        q in word.hebrew.lower()
                        or q in word.transliteration.lower()
                        or q in word.translation.lower()
                        or q in word.dstrongs.lower()
                        or q in word.root_strongs.lower()
                    ):
                        results.append(word)
                        if len(results) >= limit:
                            return results

    return results
