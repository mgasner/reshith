"""Buddhist Hybrid Sanskrit language module.

ISO 639-3 code: (no dedicated code; conventionally tagged 'bhs')

Buddhist Hybrid Sanskrit (BHS) is the literary language of early Mahayana
Buddhist texts, a Middle Indic variety heavily influenced by classical Sanskrit.
Key references include Edgerton's *Buddhist Hybrid Sanskrit Grammar and
Dictionary* (1953).  Texts use IAST-style romanisation with the same diacritics
as Sanskrit.
"""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language


class BuddhistHybridSanskritModule(LanguageModule):
    @property
    def code(self) -> str:
        return "bhs"

    @property
    def name(self) -> str:
        return "Buddhist Hybrid Sanskrit"

    @property
    def script(self) -> str:
        return "Latin (romanised)"

    def transliterate(self, text: str) -> str:
        return text

    def normalize(self, text: str) -> str:
        return unicodedata.normalize("NFC", text)


buddhist_hybrid_sanskrit = BuddhistHybridSanskritModule()
register_language(buddhist_hybrid_sanskrit)
