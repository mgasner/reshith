"""
Tokenize Rashi commentary text.

Input: raw HTML string like:
  '<b>בראשית.</b> אָמַר רַבִּי יִצְחָק...'

Output: list of (surface_text, is_bold) span tuples, then word tokens.

Key concerns:
- <b>...</b> marks the biblical lemma being commented on
- Punctuation (periods, commas, colons, parentheses, quotes) must be separated
- Nikud (U+05B0–U+05BD, U+05C1–U+05C2, U+05C4–U+05C5, U+05C7) stays attached to words
- Cantillation (U+0591–U+05AF) is stripped (irrelevant for Rashi prose)
- Maqqef (U+05BE, ־) joins two words; split on it
- Geresh (U+05F3, ׳) and Gershayim (U+05F4, ״) signal abbreviations
- Maqaf/hyphen between words is a join indicator, not punctuation
"""

from __future__ import annotations

import re
import unicodedata

CANTILLATION = set(range(0x0591, 0x05AF + 1))
NIKUD = set(range(0x05B0, 0x05BD + 1)) | {0x05C1, 0x05C2, 0x05C4, 0x05C5, 0x05C7}

# Hebrew letters
HEBREW_LETTERS = set(range(0x05D0, 0x05EA + 1))

# Punctuation characters that should be split off as separate tokens
# Punctuation to split off — deliberately excludes " and ' because those
# appear as abbreviation markers (gershayim/geresh) within Hebrew tokens.
# We only split them when they appear in isolation (not adjacent to Hebrew letters).
PUNCTUATION_CHARS = set('.,;:!?()[]{}–—\u2013\u2014\u201c\u201d\u2018\u2019')

MAQQEF = "\u05BE"  # ־
GERESH = "\u05F3"  # ׳
GERSHAYIM = "\u05F4"  # ״

# HTML tag stripper
_HTML_TAG_RE = re.compile(r"<([^>]+)>([^<]*)</\1>|<[^>]+>")
_BOLD_RE = re.compile(r"<b>(.*?)</b>", re.DOTALL)


def strip_cantillation(text: str) -> str:
    return "".join(ch for ch in text if ord(ch) not in CANTILLATION)


def strip_vowels(text: str) -> str:
    """Remove nikud and cantillation, keeping only consonants and non-Hebrew chars."""
    return "".join(ch for ch in text if ord(ch) not in CANTILLATION and ord(ch) not in NIKUD)


def is_hebrew_word(text: str) -> bool:
    return any(ord(ch) in HEBREW_LETTERS for ch in text)


def has_abbreviation_mark(text: str) -> bool:
    """Return True if the token contains geresh or gershayim."""
    return GERESH in text or GERSHAYIM in text


def parse_html_spans(html: str) -> list[tuple[str, bool]]:
    """
    Convert HTML string into a list of (text, is_bold) spans.
    Strips cantillation. Preserves nikud.
    """
    spans: list[tuple[str, bool]] = []
    pos = 0

    for m in _BOLD_RE.finditer(html):
        # Text before this bold span
        before = html[pos:m.start()]
        if before:
            spans.append((strip_cantillation(before), False))
        # Bold span content
        spans.append((strip_cantillation(m.group(1)), True))
        pos = m.end()

    # Remainder after last bold span
    tail = html[pos:]
    if tail:
        spans.append((strip_cantillation(tail), False))

    return spans


def tokenize_span(text: str, is_bold: bool) -> list[tuple[str, bool]]:
    """
    Split a text span into individual word/punctuation tokens.
    Returns list of (token_str, is_bold).
    Splits on whitespace and separates leading/trailing punctuation.
    Splits on maqqef (keeps both halves).
    """
    tokens: list[tuple[str, bool]] = []

    for raw_word in text.split():
        # Split on maqqef — treat each part separately but note the join
        parts = raw_word.split(MAQQEF)
        for i, part in enumerate(parts):
            if not part:
                continue
            # Strip leading punctuation
            while part and part[0] in PUNCTUATION_CHARS:
                tokens.append((part[0], is_bold))
                part = part[1:]
            # Strip trailing punctuation (but keep geresh/gershayim attached — they mark abbrevs)
            trailing: list[str] = []
            while part and part[-1] in PUNCTUATION_CHARS:
                trailing.insert(0, part[-1])
                part = part[:-1]
            if part:
                tokens.append((part, is_bold))
            for p in trailing:
                tokens.append((p, is_bold))

    return tokens


def tokenize_comment(html: str) -> list[tuple[str, bool]]:
    """
    Full tokenization of a single Rashi comment HTML string.
    Returns list of (surface_token, is_bold).
    """
    spans = parse_html_spans(html)
    tokens: list[tuple[str, bool]] = []
    for text, is_bold in spans:
        tokens.extend(tokenize_span(text, is_bold))
    return tokens
