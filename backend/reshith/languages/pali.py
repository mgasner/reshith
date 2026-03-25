"""Pali language module.

ISO 639-3 code: pli

Pali is the liturgical language of Theravada Buddhism, preserved in the Tipitaka
(Pali Canon).  It is closely related to Sanskrit but has undergone significant
phonological simplification.  Texts are conventionally romanised using the same
diacritical system as IAST Sanskrit (ā, ī, ū, ṃ, ṅ, ñ, ṭ, ḍ, ṇ, ḷ).
"""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language


class PaliModule(LanguageModule):
    @property
    def code(self) -> str:
        return "pli"

    @property
    def name(self) -> str:
        return "Pali"

    @property
    def script(self) -> str:
        return "Latin (romanised)"

    def transliterate(self, text: str) -> str:
        return text

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


pali = PaliModule()
register_language(pali)
