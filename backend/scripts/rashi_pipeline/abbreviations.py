"""
Rashi abbreviation expansion table.

Rashi's commentary uses many standard rabbinic abbreviations, marked with
geresh (׳) for single-letter abbreviations or gershayim (״) for multi-letter.

Sources:
- Otzar Rashei Tevot (אוצר ראשי תיבות) by Shmuel Ashkenazi & Dov Yarden
- Standard rabbinic literature conventions
- Rashi-specific usage patterns
"""

from __future__ import annotations

import re

GERESH = "\u05F3"   # ׳
GERSHAYIM = "\u05F4"  # ״

# Abbreviation lookup: normalized form (no geresh/gershayim, no nikud) → expansion
# The expansion is in Hebrew; an English gloss is provided for UI display.
# Format: { "abbrev": ("expansion_hebrew", "english_gloss") }
ABBREVIATIONS: dict[str, tuple[str, str]] = {
    # Discourse markers
    "דה": ("דיבור המתחיל", "s.v. (the cited text)"),
    "כל": ("כלומר", "that is to say"),
    "רל": ("רצוני לומר", "I mean to say"),
    "כלו": ("כלומר", "that is to say"),
    "אכ": ("אם כן", "if so"),
    "אל": ("אם לאו", "if not"),
    "ופ": ("ופירוש", "and the explanation"),
    "עכ": ("על כן", "therefore"),
    "לכ": ("לפיכך", "therefore"),
    "מה": ("מה הוא", "what is it"),
    # Source citations
    "תל": ("תלמוד לומר", "Scripture teaches"),
    "שנ": ("שנאמר", "as it says"),
    "שכ": ("שכתוב", "as it is written"),
    "כמ": ("כמו שנאמר", "as it is said"),
    "עש": ("עיין שם", "see there"),
    "עע": ("עיין עוד", "see further"),
    "כמש": ("כמו שנאמר", "as it is said"),
    "לעל": ("לעיל", "above / earlier"),
    "להל": ("להלן", "below / later"),
    # Honorifics
    "זל": ("זכרונו לברכה", "of blessed memory"),
    "עה": ("עליו השלום", "peace be upon him"),
    "עה": ("עליהם השלום", "peace be upon them"),
    "שי": ("שיחיה", "may he live"),
    "נע": ("נוחו עדן", "may he rest in Eden"),
    "הקב": ("הקדוש ברוך הוא", "the Holy One, blessed be He"),
    "הקבה": ("הקדוש ברוך הוא", "the Holy One, blessed be He"),
    "המק": ("המקום ברוך הוא", "the Omnipresent, blessed be He"),
    # Numbers / quantifiers
    "פא": ("פעם אחת", "once"),
    "כמ": ("כמה", "how many / several"),
    # Talmudic/textual terms
    "גמ": ("גמרא", "Gemara"),
    "מש": ("משנה", "Mishnah"),
    "תו": ("תוספות", "Tosafot"),
    "ור": ("ורש\"י", "and Rashi"),
    "ריף": ("רבינו יצחק אלפסי", "Alfasi"),
    "ים": ("ירושלמי", "Jerusalem Talmud"),
    "בב": ("בבלי", "Babylonian Talmud"),
    "פסי": ("פסיקתא", "Pesikta"),
    "מד": ("מדרש", "Midrash"),
    "בר": ("בראשית רבה", "Bereishit Rabbah"),
    "שמר": ("שמות רבה", "Shemot Rabbah"),
    # Grammatical terms
    "לש": ("לשון", "language of / expression"),
    "מל": ("מלשון", "from the language of"),
    "בל": ("בלשון", "in the language of"),
    "נסמ": ("נסמך", "in construct state"),
    "רבי": ("רבים", "plural"),
    "יחי": ("יחיד", "singular"),
    "זכ": ("זכר", "masculine"),
    "נק": ("נקבה", "feminine"),
    # Common phrases
    "וכ": ("וכולי", "etc."),
    "וכו": ("וכולי", "etc."),
    "אבל": ("אבל", "(but — not abbreviated)"),
    "דבר": ("דבר אחר", "another interpretation"),
    "דא": ("דבר אחר", "another interpretation"),
    "פד": ("פירוש דבר", "explanation of the matter"),
    # People
    "ר": ("רבי", "Rabbi"),
    "רב": ("רב", "Rav"),
    "רמב": ("רמב\"ם", "Maimonides"),
    "רש": ("רש\"י", "Rashi"),
    "רשב": ("רשב\"ם", "Rashbam"),
    "ריב": ("ריב\"ם", "Rivam"),
    "ר\"ת": ("רבינו תם", "Rabbenu Tam"),
    # Biblical book abbreviations (common in Rashi citations)
    "בר": ("בראשית", "Genesis"),
    "שמ": ("שמות", "Exodus"),
    "וי": ("ויקרא", "Leviticus"),
    "במ": ("במדבר", "Numbers"),
    "דב": ("דברים", "Deuteronomy"),
    "יש": ("ישעיהו", "Isaiah"),
    "יר": ("ירמיהו", "Jeremiah"),
    "תה": ("תהילים", "Psalms"),
    "מש": ("משלי", "Proverbs"),
    "אי": ("איוב", "Job"),
}


def normalize_abbreviation(token: str) -> str:
    """Remove geresh, gershayim, and nikud/cantillation for dictionary lookup."""
    # Remove geresh and gershayim
    token = token.replace(GERESH, "").replace(GERSHAYIM, "")
    # Remove nikud (U+05B0–U+05C7 range covers all Hebrew diacritics)
    token = "".join(ch for ch in token if not (0x05B0 <= ord(ch) <= 0x05C7))
    return token


def lookup_abbreviation(token: str) -> tuple[str, str] | None:
    """
    Look up an abbreviation token.
    Returns (expansion_hebrew, english_gloss) or None if not found.
    """
    key = normalize_abbreviation(token)
    return ABBREVIATIONS.get(key)


def is_abbreviation(token: str) -> bool:
    """Return True if token contains geresh or gershayim (standard abbreviation markers)."""
    return GERESH in token or GERSHAYIM in token
