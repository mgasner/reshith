"""Ancient Greek language module (covers both Classical Attic and Koine)."""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language


def strip_diacritics(text: str) -> str:
    """Remove all diacritical marks (accents, breathing marks) from Greek text."""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


class AncientGreekModule(LanguageModule):
    @property
    def code(self) -> str:
        return "grc"

    @property
    def name(self) -> str:
        return "Ancient Greek"

    @property
    def script(self) -> str:
        return "Greek"

    def transliterate(self, text: str) -> str:
        return strip_diacritics(text)

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


class KoineGreekModule(LanguageModule):
    @property
    def code(self) -> str:
        return "gnt"

    @property
    def name(self) -> str:
        return "New Testament Greek"

    @property
    def script(self) -> str:
        return "Greek"

    def transliterate(self, text: str) -> str:
        return strip_diacritics(text)

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


ancient_greek = AncientGreekModule()
register_language(ancient_greek)

koine_greek = KoineGreekModule()
register_language(koine_greek)
