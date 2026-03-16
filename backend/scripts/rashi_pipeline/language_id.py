"""
Language identification for Rashi tokens.

Rashi's commentary mixes:
1. Biblical Hebrew
2. Mishnaic/Rabbinic Hebrew
3. Jewish Babylonian Aramaic
4. Old French (לעז / laaz) — written in Hebrew characters
5. Occasional Latin/Greek technical terms

Detection strategy:
- Abbreviations: detected via geresh/gershayim marks (see abbreviations.py)
- Old French: heuristic — follows a "laaz marker" token (לעז, בלעז, שקורין, etc.)
- Aramaic: lexical heuristics + known Aramaic morphological features
- Hebrew: default for everything else

Aramaic heuristics (this is the hardest part):
- Ends in א (aleph) as definite article: דמלכא, ארעא, שמיא
- Common Aramaic words: דא, הא, מאי, אמאי, דכד, מן, עד, כי, הוי, ליה, לה
- Aramaic verb forms: endings like ין, ן (3pl impf), ית (2sg perf), ינא (1sg impf)
- Aramaic particles: דלא, דהוי, כד, עד דלא
- Dictionaries (Jastrow vs BDB) are the real arbiter; we flag for human review

Note: Perfect detection is impossible without full morphological analysis.
We use a "suspicion score" approach — if enough signals are present, flag as Aramaic.
"""

from __future__ import annotations

import re

from .abbreviations import is_abbreviation
from .models import Language

# Tokens that signal the next N tokens are Old French (laaz)
LAAZ_MARKERS = {
    "לעז", "בלעז", "שקורין", "שנקרא", "שנקראת", "שקורין", "שאמרו", "בלעז",
    "שבלעז", "פי׳", "פירוש",  # sometimes פירוש introduces a gloss too
}

# Normalize marker lookup (strip nikud)
def _strip_nikud(s: str) -> str:
    return "".join(ch for ch in s if not (0x05B0 <= ord(ch) <= 0x05C7))


LAAZ_MARKERS_NORMALIZED = {_strip_nikud(m) for m in LAAZ_MARKERS}

# Definitive Aramaic function words (normalized, no nikud)
ARAMAIC_FUNCTION_WORDS = {
    "דא", "הא", "הוא", "היא", "הני", "הנך", "הכי", "הכא", "התם", "הכא",
    "מאי", "אמאי", "למאי", "היכי", "כיצד",  # כיצד is actually Heb/Aram both
    "כד", "עד", "כי", "די", "דלא", "דהוה", "דהוי",
    "ליה", "לה", "לן", "להו",
    "ביה", "בה",
    # NOTE: בהו removed — too easily confused with Biblical Hebrew תֹּהוּ וָבֹהוּ
    "מיניה", "מינה", "מינייהו",
    "קמיה", "קמה", "קמן",
    "גביה", "גבה",
    "מאן", "דמאן",
    "איכא", "ליכא",
    "הוה", "הוי", "הויא", "הוין",
    # NOTE: אמר/אמרי/אמרינן deliberately excluded — too common in Hebrew
    # to use as an Aramaic signal without wider context
    "בעי", "בעינן",
    "אזל", "אתא", "אייתי",
    "שרי", "אסר",
    "חזי", "חזינן",
    "תא", "תו",
    "דרב", "דרבי",  # genitive constructions
    "כולהו", "כולי", "כולא",
    "עלמא", "עלמין",
    "שמיא", "ארעא", "מיא",
    "מלתא", "מילתא", "מילי",
    "הוא", "היא", "אינהו", "אינון",
    "אלא", "אלמא",
    "פשיטא", "תיקו", "תיקא",
    "אביי", "רבא",  # common Talmudic names (context clue)
}

# Words that end in aleph and are Aramaic definite state
_ALEPH_DEFINITE_WORDS_RE = re.compile(r"[\u05D0-\u05EA]{2,}א$")

# Hebrew-only function words (contra-indicators for Aramaic)
HEBREW_FUNCTION_WORDS = {
    "אשר", "כאשר", "אשר", "כי", "ואשר", "לאשר",
    "הנה", "הנני", "אני", "אנכי",
    "אתה", "אתם", "אתן",
    "הוא", "היא", "הם", "הן",
    "כל", "כלל",
}


def _normalize(token: str) -> str:
    return "".join(ch for ch in token if not (0x05B0 <= ord(ch) <= 0x05C7))


def _is_aramaic_word(token: str) -> bool:
    norm = _normalize(token)
    if norm in ARAMAIC_FUNCTION_WORDS:
        return True
    # Ends in aleph (common Aramaic definite): at least 3 chars
    if len(norm) >= 3 and norm.endswith("א") and norm not in HEBREW_FUNCTION_WORDS:
        # Extra check: not a known Hebrew word ending in aleph
        # (e.g. קרא, ירא, צמא are Biblical Hebrew) — we can't be definitive here
        return True
    return False


def _aramaic_suspicion_score(token: str) -> float:
    """Return a score 0.0–1.0 indicating how Aramaic-like a token is."""
    norm = _normalize(token)
    score = 0.0

    if norm in ARAMAIC_FUNCTION_WORDS:
        score += 0.9

    # Definite state aleph ending
    if len(norm) >= 3 and norm.endswith("א"):
        score += 0.3

    # Aramaic 3pl ending ין
    if norm.endswith("ין"):
        score += 0.2

    # Aramaic suffix ית (2sg perf)
    if norm.endswith("ית") and len(norm) > 3:
        score += 0.15

    # Aramaic genitive ד prefix
    if norm.startswith("ד") and len(norm) > 2:
        score += 0.1

    return min(score, 1.0)


class LanguageIdentifier:
    """
    Stateful language identifier — tracks context across tokens
    so that laaz markers trigger Old French tagging for subsequent tokens.
    """

    ARAMAIC_THRESHOLD = 0.4  # suspicion score above which we flag as Aramaic
    LAAZ_WINDOW = 3  # number of tokens after a laaz marker to tag as Old French

    def __init__(self) -> None:
        self._laaz_remaining = 0  # how many more tokens to tag as Old French

    def reset(self) -> None:
        """Call at the start of each new verse/comment."""
        self._laaz_remaining = 0

    def identify(self, token: str) -> Language:
        """
        Identify the language of a single token.
        Call in order — state carries across tokens within a comment.
        """
        from .tokenizer import is_hebrew_word, PUNCTUATION_CHARS

        # Punctuation
        if len(token) == 1 and token in PUNCTUATION_CHARS:
            return Language.PUNCTUATION

        # Abbreviation (geresh/gershayim marks)
        if is_abbreviation(token):
            return Language.ABBREVIATION

        # Not a Hebrew-script word at all
        if not is_hebrew_word(token):
            return Language.UNKNOWN

        norm = _normalize(token)

        # Check if we're in a laaz window
        if self._laaz_remaining > 0:
            self._laaz_remaining -= 1
            return Language.OLD_FRENCH

        # Check if this token is a laaz marker
        if norm in LAAZ_MARKERS_NORMALIZED:
            self._laaz_remaining = self.LAAZ_WINDOW
            # The marker itself is Hebrew
            return Language.HEBREW

        # Aramaic suspicion
        if _aramaic_suspicion_score(norm) >= self.ARAMAIC_THRESHOLD:
            return Language.ARAMAIC

        return Language.HEBREW
