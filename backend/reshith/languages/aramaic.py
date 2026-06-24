"""Aramaic language module.

ISO 639-3 code: arc (Official/Imperial Aramaic)

Aramaic is the language of the Targumim, portions of Daniel and Ezra, the
Talmud, and the Zohar.  It shares the Hebrew/Aramaic square script and is
written right-to-left.  The transliteration scheme follows the same conventions
as Biblical Hebrew, with additional characters for Aramaic-specific forms.
"""

import unicodedata

from reshith.languages.base import CANTILLATION_RANGE, LanguageModule
from reshith.languages.registry import register_language


class AramaicModule(LanguageModule):
    @property
    def code(self) -> str:
        return "arc"

    @property
    def name(self) -> str:
        return "Aramaic"

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


aramaic = AramaicModule()
register_language(aramaic)
