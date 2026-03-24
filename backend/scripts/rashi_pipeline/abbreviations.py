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

GERESH = "\u05F3"   # ׳  (Hebrew geresh)
GERSHAYIM = "\u05F4"  # ״  (Hebrew gershayim)
# ASCII equivalents appear frequently in the source text
_ABBREV_CHARS = frozenset([GERESH, GERSHAYIM, '"', "'"])

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
    "כמ": ("כמו שנאמר / כמה", "as it is said / how many"),
    "עש": ("עיין שם", "see there"),
    "עע": ("עיין עוד", "see further"),
    "כמש": ("כמו שנאמר", "as it is said"),
    "לעל": ("לעיל", "above / earlier"),
    "להל": ("להלן", "below / later"),
    # Honorifics
    "זל": ("זכרונו לברכה", "of blessed memory"),
    "עה": ("עליו השלום / עליהם השלום", "peace be upon him/them"),
    "שי": ("שיחיה", "may he live"),
    "נע": ("נוחו עדן", "may he rest in Eden"),
    "הקב": ("הקדוש ברוך הוא", "the Holy One, blessed be He"),
    "הקבה": ("הקדוש ברוך הוא", "the Holy One, blessed be He"),
    "המק": ("המקום ברוך הוא", "the Omnipresent, blessed be He"),
    # Numbers / quantifiers
    "פא": ("פעם אחת", "once"),
    # Talmudic/textual terms
    "גמ": ("גמרא", "Gemara"),
    "מש": ("משנה / משלי", "Mishnah / Proverbs"),
    "תו": ("תוספות", "Tosafot"),
    "ור": ("ורש\"י", "and Rashi"),
    "ריף": ("רבינו יצחק אלפסי", "Alfasi"),
    "ים": ("ירושלמי", "Jerusalem Talmud"),
    "בב": ("בבלי", "Babylonian Talmud"),
    "פסי": ("פסיקתא", "Pesikta"),
    "מד": ("מדרש", "Midrash"),
    "בר": ("בראשית רבה / בראשית", "Bereishit Rabbah / Genesis"),
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
    "וג": ("וגו׳ (וגומר)", "etc. (and so on — biblical citation continues)"),
    "וגו": ("וגומר", "and so on (biblical citation continues)"),
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
    "שמ": ("שמות", "Exodus"),
    "וי": ("ויקרא", "Leviticus"),
    "במ": ("במדבר", "Numbers"),
    "דב": ("דברים", "Deuteronomy"),
    "יש": ("ישעיהו", "Isaiah"),
    "יר": ("ירמיהו", "Jeremiah"),
    "תה": ("תהילים", "Psalms"),
    "אי": ("איוב", "Job"),
}


def normalize_abbreviation(token: str) -> str:
    """Remove geresh, gershayim, ASCII quotes, and nikud for dictionary lookup."""
    token = "".join(ch for ch in token if ch not in _ABBREV_CHARS)
    # Remove nikud (U+05B0–U+05C7 range covers all Hebrew diacritics)
    token = "".join(ch for ch in token if not (0x05B0 <= ord(ch) <= 0x05C7))
    return token


def _is_numeric_reference(normalized: str) -> bool:
    """
    Return True if this looks like a biblical chapter/verse number written
    in Hebrew numerals with gershayim. Examples: קי"א (111), כ"ז (27), ח' (8).
    Hebrew numbers use the letter values: א=1 יוד=10 ק=100 etc.
    We detect the pattern: optional hundreds letter + optional tens + units.
    """
    # Hebrew numeric letters
    numeric = set("אבגדהוזחטיכלמנסעפצקרש")
    return all(ch in numeric for ch in normalized) and 1 <= len(normalized) <= 4


def lookup_abbreviation(token: str) -> tuple[str, str] | None:
    """
    Look up an abbreviation token.
    Returns (expansion_hebrew, english_gloss) or None if not found.
    """
    key = normalize_abbreviation(token)
    if key in ABBREVIATIONS:
        return ABBREVIATIONS[key]
    # Detect Hebrew numeral references (biblical chapter/verse citations)
    if _is_numeric_reference(key):
        return (key, "biblical chapter/verse number")
    return None


# Full words that contain quote chars but are NOT abbreviations.
# Typically words where the " is a vowel-marker or scribal convention.
_NOT_ABBREVIATIONS: frozenset[str] = frozenset([
    "בלעז",    # "in a foreign language" — not an abbreviation despite the "
    "וגו",     # וְגוֹ׳ / וגו' = "and so on" — treated as its own abbreviation below
])


def is_abbreviation(token: str) -> bool:
    """
    Return True if token is a Hebrew abbreviation (has an abbreviation mark
    AND is short enough to plausibly be an abbreviation rather than a long
    Old French/other-language word written in Hebrew characters).

    Rashi's abbreviations are almost always 2–5 Hebrew letters total.
    Old French glosses written in Hebrew script are typically longer (6+ letters)
    and also contain quote-chars but are NOT abbreviations.
    """
    if not any(ch in _ABBREV_CHARS for ch in token):
        return False
    # Count only Hebrew letters (no diacritics, no quote chars)
    hebrew_letters = [ch for ch in token if 0x05D0 <= ord(ch) <= 0x05EA]
    if not hebrew_letters:
        return False
    # Long tokens (6+ Hebrew letters) are likely Old French glosses or foreign words
    if len(hebrew_letters) >= 6:
        return False
    # Check against known full words that happen to contain quote chars
    normalized = normalize_abbreviation(token)
    if normalized in _NOT_ABBREVIATIONS:
        return False
    return True
