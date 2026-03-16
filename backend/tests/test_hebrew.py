"""Tests for Biblical Hebrew language module."""

from reshith.languages.hebrew import biblical_hebrew


def test_transliterate_basic():
    result = biblical_hebrew.transliterate("אבגדה")
    assert result == "ʾbgdh"


def test_transliterate_with_final_forms():
    result = biblical_hebrew.transliterate("מלך")
    assert result == "mlk"


def test_rtl():
    assert biblical_hebrew.rtl is True


def test_code():
    assert biblical_hebrew.code == "hbo"


def test_strip_vowels():
    text_with_vowels = "בְּרֵאשִׁית"
    result = biblical_hebrew.strip_vowels(text_with_vowels)
    assert result == "בראשית"
