"""Tests for auto-building vocab decks from Biblical passage references."""

import unicodedata

import pytest

from reshith.db import models
from reshith.services import deck_from_passage as dfp


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


# ---------------------------------------------------------------------------
# Reference parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,book,corpus,c1,v1,c2,v2",
    [
        ("Genesis 1:1-2:3", "Gen", "hbo", 1, 1, 2, 3),
        ("Gen 1", "Gen", "hbo", 1, 0, 1, dfp._TO_END),
        ("John 1:1-18", "Jhn", "gnt", 1, 1, 1, 18),
        ("1 Cor 13", "1Co", "gnt", 13, 0, 13, dfp._TO_END),
        ("Ps 23", "Psa", "hbo", 23, 0, 23, dfp._TO_END),
        ("Jhn 3:16", "Jhn", "gnt", 3, 16, 3, 16),
        ("1John 1:1", "1Jn", "gnt", 1, 1, 1, 1),
        ("Exod. 20:1-17", "Exo", "hbo", 20, 1, 20, 17),
    ],
)
def test_parse_reference(text, book, corpus, c1, v1, c2, v2):
    ref = dfp.parse_reference(text)
    assert ref.book == book
    assert ref.corpus == corpus
    assert (ref.start_chapter, ref.start_verse) == (c1, v1)
    assert (ref.end_chapter, ref.end_verse) == (c2, v2)


def test_parse_reference_language():
    assert dfp.parse_reference("Gen 1").language == models.LanguageCode.BIBLICAL_HEBREW
    assert dfp.parse_reference("Jhn 1").language == models.LanguageCode.NT_GREEK


def test_parse_reference_dash_variants():
    # En-dash and spaced hyphen both work.
    assert dfp.parse_reference("Gen 1:1\u20133").end_verse == 3
    assert dfp.parse_reference("Gen 1:1 - 3").end_verse == 3


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "Frobnicate 1", "Genesis", "Gen 3:5-3:1", "Gen 5:10-2:1"],
)
def test_parse_reference_rejects_bad_input(bad):
    with pytest.raises(dfp.ReferenceError):
        dfp.parse_reference(bad)


def test_display_normalisation():
    assert dfp.parse_reference("gen 1").display == "Genesis 1"
    assert dfp.parse_reference("Gen 1:1-2:3").display == "Genesis 1:1-2:3"
    assert dfp.parse_reference("Jhn 3:16").display == "John 3:16"
    assert dfp.parse_reference("1 cor 13").display == "1 Corinthians 13"


# ---------------------------------------------------------------------------
# Seed building (requires TAHOT/GNT data present in the repo)
# ---------------------------------------------------------------------------


def test_build_seeds_hebrew():
    ref = dfp.parse_reference("Gen 1:1")
    seeds = dfp.build_seeds_for_passage(ref)
    assert seeds, "expected vocab for Genesis 1:1"
    lemmas = {_nfc(s.lemma) for s in seeds}
    # אֱלֹהִים (God) appears in Gen 1:1.
    assert _nfc("\u05d0\u05b1\u05dc\u05b9\u05d4\u05b4\u05d9\u05dd") in lemmas
    for s in seeds:
        assert s.lemma
        assert s.definition  # every card has a back


def test_build_seeds_greek():
    ref = dfp.parse_reference("John 1:1")
    seeds = dfp.build_seeds_for_passage(ref)
    by_lemma = {_nfc(s.lemma): s for s in seeds}
    logos = by_lemma[_nfc("\u03bb\u03cc\u03b3\u03bf\u03c2")]  # λόγος
    assert "word" in logos.definition.lower()
    assert logos.transliteration
    assert logos.notes and "Strong's" in logos.notes


def test_build_seeds_dedups_by_lemma():
    # A chapter has many repeated words; distinct lemmas must be far fewer
    # than the running token count, and strictly unique.
    ref = dfp.parse_reference("Gen 1")
    seeds = dfp.build_seeds_for_passage(ref)
    lemmas = [s.lemma for s in seeds]
    assert len(lemmas) == len(set(lemmas))
    assert len(lemmas) > 20  # non-trivial vocab


def test_build_seeds_preserves_first_appearance_order():
    ref = dfp.parse_reference("Jhn 1:1")
    seeds = dfp.build_seeds_for_passage(ref)
    # John 1:1 opens with Ἐν ἀρχῇ (ἐν, ἀρχή) — those lemmas come first.
    assert _nfc(seeds[0].lemma) == _nfc("\u1f10\u03bd")            # ἐν
    assert _nfc(seeds[1].lemma) == _nfc("\u1f00\u03c1\u03c7\u03ae")  # ἀρχή
