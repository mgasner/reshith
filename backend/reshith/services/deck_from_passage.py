"""Build vocabulary decks automatically from Biblical passages.

Given a free-form reference like ``Genesis 1:1-2:3`` or ``John 1:1-18`` this
module walks the tagged text (TAHOT for the Hebrew OT, GNT for the Greek NT),
collapses every inflected token down to its lemma (via its head Strong's
number), and produces one :class:`~reshith.services.primary_deck.VocabSeed`
per distinct lemma — glossed, transliterated, and lightly parsed from the
Tyndale Strong's lexicon (TBESH/TBESG).

The public entry point is :func:`build_seeds_for_passage`, which the GraphQL
``createDeckFromPassage`` mutation calls before handing the seeds to
``primary_deck.ensure_cards_for_vocab``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from reshith.db import models
from reshith.services import gnt, tahot, tbesh
from reshith.services.primary_deck import VocabSeed

# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------

# Human book name / common abbreviation -> canonical TAHOT/GNT abbreviation.
# Lower-cased, punctuation-stripped keys; leading numerals normalised to digits.
_BOOK_ALIASES: dict[str, tuple[str, str]] = {}


def _register(abbrev: str, corpus: str, *names: str) -> None:
    for n in (abbrev, *names):
        _BOOK_ALIASES[_norm_book_key(n)] = (abbrev, corpus)


def _norm_book_key(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("1st", "1").replace("2nd", "2").replace("3rd", "3")
    s = re.sub(r"\bfirst\b", "1", s)
    s = re.sub(r"\bsecond\b", "2", s)
    s = re.sub(r"\bthird\b", "3", s)
    s = re.sub(r"[.\s]+", "", s)
    return s


# Hebrew OT (TAHOT)
_register("Gen", "hbo", "Genesis", "Gn")
_register("Exo", "hbo", "Exodus", "Ex", "Exod")
_register("Lev", "hbo", "Leviticus", "Lv")
_register("Num", "hbo", "Numbers", "Nm", "Nu")
_register("Deu", "hbo", "Deuteronomy", "Dt", "Deut")
_register("Jos", "hbo", "Joshua", "Josh")
_register("Jdg", "hbo", "Judges", "Jdgs")
_register("1Sa", "hbo", "1Samuel", "1Sam", "1Sm")
_register("2Sa", "hbo", "2Samuel", "2Sam", "2Sm")
_register("1Ki", "hbo", "1Kings", "1Kgs")
_register("2Ki", "hbo", "2Kings", "2Kgs")
_register("1Ch", "hbo", "1Chronicles", "1Chr", "1Chron")
_register("2Ch", "hbo", "2Chronicles", "2Chr", "2Chron")
_register("Ezr", "hbo", "Ezra")
_register("Neh", "hbo", "Nehemiah")
_register("Est", "hbo", "Esther", "Esth")
_register("Job", "hbo", "Job")
_register("Psa", "hbo", "Psalms", "Psalm", "Ps", "Pss")
_register("Pro", "hbo", "Proverbs", "Prov", "Prv")
_register("Ecc", "hbo", "Ecclesiastes", "Eccl", "Qoheleth")
_register("Sng", "hbo", "SongofSongs", "Song", "SongofSolomon", "Canticles")
_register("Isa", "hbo", "Isaiah", "Is")
_register("Jer", "hbo", "Jeremiah")
_register("Lam", "hbo", "Lamentations")
_register("Ezk", "hbo", "Ezekiel", "Ezek", "Eze")
_register("Dan", "hbo", "Daniel")
_register("Hos", "hbo", "Hosea")
_register("Jol", "hbo", "Joel")
_register("Amo", "hbo", "Amos")
_register("Oba", "hbo", "Obadiah", "Obad")
_register("Jon", "hbo", "Jonah")
_register("Mic", "hbo", "Micah")
_register("Nah", "hbo", "Nahum")
_register("Hab", "hbo", "Habakkuk")
_register("Zep", "hbo", "Zephaniah", "Zeph")
_register("Hag", "hbo", "Haggai")
_register("Zec", "hbo", "Zechariah", "Zech")
_register("Mal", "hbo", "Malachi")

# Greek NT (GNT)
_register("Mat", "gnt", "Matthew", "Mt", "Matt")
_register("Mrk", "gnt", "Mark", "Mk")
_register("Luk", "gnt", "Luke", "Lk")
_register("Jhn", "gnt", "John", "Jn")
_register("Act", "gnt", "Acts")
_register("Rom", "gnt", "Romans", "Ro")
_register("1Co", "gnt", "1Corinthians", "1Cor")
_register("2Co", "gnt", "2Corinthians", "2Cor")
_register("Gal", "gnt", "Galatians")
_register("Eph", "gnt", "Ephesians")
_register("Php", "gnt", "Philippians", "Phil")
_register("Col", "gnt", "Colossians")
_register("1Th", "gnt", "1Thessalonians", "1Thess")
_register("2Th", "gnt", "2Thessalonians", "2Thess")
_register("1Ti", "gnt", "1Timothy", "1Tim")
_register("2Ti", "gnt", "2Timothy", "2Tim")
_register("Tit", "gnt", "Titus")
_register("Phm", "gnt", "Philemon", "Phlm")
_register("Heb", "gnt", "Hebrews")
_register("Jas", "gnt", "James", "Jm")
_register("1Pe", "gnt", "1Peter", "1Pet", "1Pt")
_register("2Pe", "gnt", "2Peter", "2Pet", "2Pt")
_register("1Jn", "gnt", "1John")
_register("2Jn", "gnt", "2John")
_register("3Jn", "gnt", "3John")
_register("Jud", "gnt", "Jude")
_register("Rev", "gnt", "Revelation", "Rv", "Apocalypse")

_HUMAN_BOOK_NAMES: dict[str, str] = {
    "Gen": "Genesis", "Exo": "Exodus", "Lev": "Leviticus", "Num": "Numbers",
    "Deu": "Deuteronomy", "Jos": "Joshua", "Jdg": "Judges", "1Sa": "1 Samuel",
    "2Sa": "2 Samuel", "1Ki": "1 Kings", "2Ki": "2 Kings", "1Ch": "1 Chronicles",
    "2Ch": "2 Chronicles", "Ezr": "Ezra", "Neh": "Nehemiah", "Est": "Esther",
    "Job": "Job", "Psa": "Psalms", "Pro": "Proverbs", "Ecc": "Ecclesiastes",
    "Sng": "Song of Songs", "Isa": "Isaiah", "Jer": "Jeremiah",
    "Lam": "Lamentations", "Ezk": "Ezekiel", "Dan": "Daniel", "Hos": "Hosea",
    "Jol": "Joel", "Amo": "Amos", "Oba": "Obadiah", "Jon": "Jonah",
    "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk", "Zep": "Zephaniah",
    "Hag": "Haggai", "Zec": "Zechariah", "Mal": "Malachi",
    "Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John",
    "Act": "Acts", "Rom": "Romans", "1Co": "1 Corinthians", "2Co": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Php": "Philippians", "Col": "Colossians",
    "1Th": "1 Thessalonians", "2Th": "2 Thessalonians", "1Ti": "1 Timothy",
    "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon", "Heb": "Hebrews",
    "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter", "1Jn": "1 John",
    "2Jn": "2 John", "3Jn": "3 John", "Jud": "Jude", "Rev": "Revelation",
}


class ReferenceError(ValueError):
    """Raised when a passage reference can't be parsed or found."""


@dataclass(frozen=True)
class PassageRef:
    corpus: str          # "hbo" or "gnt"
    book: str            # canonical abbreviation, e.g. "Gen"
    start_chapter: int
    start_verse: int     # 0 => from start of chapter
    end_chapter: int
    end_verse: int       # a large sentinel => to end of chapter

    @property
    def language(self) -> models.LanguageCode:
        return (
            models.LanguageCode.BIBLICAL_HEBREW
            if self.corpus == "hbo"
            else models.LanguageCode.NT_GREEK
        )

    @property
    def display(self) -> str:
        name = _HUMAN_BOOK_NAMES.get(self.book, self.book)
        whole_end = self.end_verse >= _TO_END
        if self.start_chapter == self.end_chapter:
            if self.start_verse <= 1 and whole_end:
                return f"{name} {self.start_chapter}"
            start_v = self.start_verse or 1
            if whole_end:
                return f"{name} {self.start_chapter}:{start_v}-end"
            if self.end_verse == start_v:
                return f"{name} {self.start_chapter}:{start_v}"
            return f"{name} {self.start_chapter}:{start_v}-{self.end_verse}"
        end_v = "end" if whole_end else str(self.end_verse)
        return (
            f"{name} {self.start_chapter}:{self.start_verse or 1}"
            f"-{self.end_chapter}:{end_v}"
        )


_TO_END = 10_000

# Book (letters/digits, possibly spaced like "1 John") then an optional
# chapter[:verse][-chapter[:verse]] tail.
_REF_RE = re.compile(
    r"""^\s*
        (?P<book>(?:[1-3]\s*)?[A-Za-z][A-Za-z. ]*?)   # book name
        \s*
        (?:
            (?P<c1>\d+)
            (?::(?P<v1>\d+))?
            (?:\s*[-\u2013]\s*
                (?:(?P<c2>\d+):)?     # optional end chapter
                (?P<v2>\d+)
            )?
        )?
    \s*$""",
    re.VERBOSE,
)


def parse_reference(text: str) -> PassageRef:
    """Parse a free-form reference into a normalised :class:`PassageRef`.

    Accepts things like ``Genesis 1``, ``Gen 1:1-2:3``, ``John 1:1-18``,
    ``1 Cor 13``, ``Ps 23``. A bare book+chapter covers the whole chapter;
    a bare book (no chapter) is rejected.
    """
    if not text or not text.strip():
        raise ReferenceError("Empty reference.")

    m = _REF_RE.match(text)
    if not m:
        raise ReferenceError(f"Couldn't parse reference: {text!r}")

    book_raw = m.group("book")
    key = _norm_book_key(book_raw)
    if key not in _BOOK_ALIASES:
        raise ReferenceError(f"Unknown book: {book_raw.strip()!r}")
    abbrev, corpus = _BOOK_ALIASES[key]

    if m.group("c1") is None:
        raise ReferenceError(
            f"Need at least a chapter, e.g. '{book_raw.strip()} 1'."
        )

    c1 = int(m.group("c1"))
    v1 = int(m.group("v1")) if m.group("v1") else 0
    has_verse = m.group("v1") is not None

    # Resolve the end of the range.
    if m.group("v2") is not None:
        v2 = int(m.group("v2"))
        c2 = int(m.group("c2")) if m.group("c2") else c1
    else:
        # No explicit end: whole chapter if no start verse, else single verse.
        c2 = c1
        v2 = v1 if has_verse else _TO_END

    if not has_verse:
        v1 = 0  # from the top of the chapter

    if (c2, v2) < (c1, v1):
        raise ReferenceError("Reference end precedes its start.")

    return PassageRef(
        corpus=corpus,
        book=abbrev,
        start_chapter=c1,
        start_verse=v1,
        end_chapter=c2,
        end_verse=v2,
    )


# ---------------------------------------------------------------------------
# Word collection
# ---------------------------------------------------------------------------

# TAHOT/GNT text_type codes we skip: Q(ere)/K(etiv) alternates duplicate the
# main (L) reading; keeping both would double-count. We keep L and X.
_SKIP_TEXT_TYPES = {"Q", "K"}


def _iter_words(ref: PassageRef):
    """Yield tagged words for the passage in reading order."""
    corpus = tahot if ref.corpus == "hbo" else gnt
    get_chapter = corpus.get_chapter
    get_verse = corpus.get_verse

    for ch in range(ref.start_chapter, ref.end_chapter + 1):
        verses = get_chapter(ref.book, ch)
        if not verses:
            continue
        lo = ref.start_verse if ch == ref.start_chapter else 0
        hi = ref.end_verse if ch == ref.end_chapter else _TO_END
        for v in sorted(verses):
            if v < lo or v > hi:
                continue
            yield from get_verse(ref.book, ch, v)


# ---------------------------------------------------------------------------
# Lemma resolution
# ---------------------------------------------------------------------------

_BRACES_RE = re.compile(r"[{}]")
_DISAMBIG_RE = re.compile(r"_[A-Z]$")


def _head_strongs(word) -> str:
    """Return the head-lemma Strong's ID for a tagged word.

    Prefers ``root_strongs`` (already the lexical head for morpheme-segmented
    Hebrew words); falls back to the last sub-token of ``dstrongs`` (for a
    prefixed word that's the lexical head, not the prefix particle).
    """
    root = getattr(word, "root_strongs", "") or ""
    if root:
        return _DISAMBIG_RE.sub("", _BRACES_RE.sub("", root).strip())
    d = (getattr(word, "dstrongs", "") or "").strip()
    d = _BRACES_RE.sub("", d)
    parts = [p for p in d.split("/") if p]
    if not parts:
        return ""
    return _DISAMBIG_RE.sub("", parts[-1])


def _surface(word) -> str:
    return getattr(word, "hebrew", None) or getattr(word, "greek", "") or ""


def build_seeds_for_passage(ref: PassageRef) -> list[VocabSeed]:
    """Collect one :class:`VocabSeed` per distinct lemma in the passage.

    Lemmas are ordered by first appearance. Each seed's ``lemma`` is the
    dictionary (lexicon) form so cards dedup across inflected occurrences and
    line up with the rest of the SRS system's ``vocab_id(language, lemma)``
    keys.
    """
    seen: set[str] = set()
    seeds: list[VocabSeed] = []

    for word in _iter_words(ref):
        if getattr(word, "text_type", "") in _SKIP_TEXT_TYPES:
            continue
        strongs = _head_strongs(word)
        if not strongs:
            continue
        entry = tbesh.get_entry(strongs)

        lemma = (entry.native if entry else "").strip() or _surface(word).strip()
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)

        definition = (entry.gloss if entry and entry.gloss else "").strip()
        if not definition:
            definition = (getattr(word, "translation", "") or "").strip()

        transliteration = (
            (entry.transliteration if entry else "")
            or getattr(word, "transliteration", "")
            or ""
        ).strip() or None

        parsing = (getattr(word, "grammar", "") or "").strip()
        morph = (entry.morph if entry else "").strip()
        grammatical_info = parsing or morph or None

        notes_bits = []
        if strongs:
            notes_bits.append(f"Strong's {strongs}")
        if morph and parsing and morph != parsing:
            notes_bits.append(morph)
        notes = " \u00b7 ".join(notes_bits) or None

        seeds.append(
            VocabSeed(
                lemma=lemma,
                definition=definition,
                transliteration=transliteration,
                category=grammatical_info,
                lesson=None,
                notes=notes,
            )
        )

    return seeds
