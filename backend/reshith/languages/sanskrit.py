"""Sanskrit language module."""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language

# IAST diacritics used for Sanskrit transliteration
IAST_CHARS = set("āīūṛṝḷḹṃḥśṣṭḍṇñṅ")


def strip_iast(text: str) -> str:
    """Remove IAST diacritics for loose comparison."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped).lower()


class SanskritModule(LanguageModule):
    @property
    def code(self) -> str:
        return "san"

    @property
    def name(self) -> str:
        return "Sanskrit"

    @property
    def script(self) -> str:
        return "Devanagari"

    def transliterate(self, text: str) -> str:
        # Sanskrit is typically transliterated via IAST — stored in the data
        return text

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


sanskrit = SanskritModule()
register_language(sanskrit)
