"""Midrashic Hebrew language module.

ISO 639-3 code: heb (Modern/Mishnaic Hebrew — used here for the post-biblical
literary register found in Midrash, Mishnah, and other rabbinic texts)

Midrashic Hebrew shares the square script with Biblical Hebrew but has a
distinct vocabulary, grammar (e.g., increased use of the participle as a
present tense), and orthographic conventions.  Normalization strips cantillation
marks following the same logic as the Biblical Hebrew module.
"""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language

CANTILLATION_RANGE = range(0x0591, 0x05AF + 1)


class MidrashicHebrewModule(LanguageModule):
    @property
    def code(self) -> str:
        return "heb"

    @property
    def name(self) -> str:
        return "Midrashic Hebrew"

    @property
    def script(self) -> str:
        return "Hebrew"

    @property
    def rtl(self) -> bool:
        return True

    def transliterate(self, text: str) -> str:
        return text

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        result = []
        for char in text:
            if ord(char) not in CANTILLATION_RANGE:
                result.append(char)
        return "".join(result)


midrashic_hebrew = MidrashicHebrewModule()
register_language(midrashic_hebrew)
