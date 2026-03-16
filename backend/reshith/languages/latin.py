"""Latin language module."""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language

# Macron vowels used in Latin notation
MACRON_MAP = {
    "ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u",
    "Ā": "A", "Ē": "E", "Ī": "I", "Ō": "O", "Ū": "U",
}


class LatinModule(LanguageModule):
    @property
    def code(self) -> str:
        return "lat"

    @property
    def name(self) -> str:
        return "Latin"

    @property
    def script(self) -> str:
        return "Latin"

    @property
    def rtl(self) -> bool:
        return False

    def transliterate(self, text: str) -> str:
        # Latin is already in Latin script; strip macrons for a bare-ASCII form
        return self.normalize(text)

    def normalize(self, text: str) -> str:
        # Remove macrons: decompose, drop combining diacritical marks, recompose
        decomposed = unicodedata.normalize("NFD", text)
        stripped = "".join(
            ch for ch in decomposed if unicodedata.category(ch) != "Mn"
        )
        return unicodedata.normalize("NFC", stripped)


latin = LatinModule()
register_language(latin)


def strip_macrons(text: str) -> str:
    """Remove macrons from Latin text."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


class EcclesiasticalLatinModule(LanguageModule):
    @property
    def code(self) -> str:
        return "ecl"

    @property
    def name(self) -> str:
        return "Ecclesiastical Latin"

    @property
    def script(self) -> str:
        return "Latin"

    def normalize(self, text: str) -> str:
        return strip_macrons(text)

    def transliterate(self, text: str) -> str:
        return text


ecclesiastical_latin = EcclesiasticalLatinModule()
register_language(ecclesiastical_latin)
