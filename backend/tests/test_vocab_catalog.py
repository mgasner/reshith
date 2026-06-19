"""Smoke tests for the cross-language vocab catalogue."""

from reshith.db import models
from reshith.services import vocab_catalog


def test_total_lessons_hebrew():
    # Lessons 1–5 ship in repo.
    assert vocab_catalog.total_lessons(models.LanguageCode.BIBLICAL_HEBREW) >= 1


def test_load_vocab_hebrew_returns_seeds():
    seeds = vocab_catalog.load_vocab(models.LanguageCode.BIBLICAL_HEBREW, 1)
    assert len(seeds) > 0
    first = seeds[0]
    assert first.lemma
    assert first.definition
    assert first.lesson == 1


def test_load_vocab_unknown_language_returns_empty():
    assert vocab_catalog.load_vocab(models.LanguageCode.PALI, 1) == []
