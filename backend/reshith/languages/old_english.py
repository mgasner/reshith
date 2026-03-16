"""Old English (Anglo-Saxon) language module.

ISO 639-3 code: ang

Old English is the earliest attested form of the English language, spoken in
England and parts of Scotland from the mid-5th century to the mid-12th century.
It is the language of Beowulf, the Anglo-Saxon Chronicle, and the works of
Ælfric and Wulfstan.

Special characters:
  þ (thorn)  — represents /θ/ as in 'thin'
  ð (eth)    — represents /ð/ as in 'this' (interchangeable with þ in manuscripts)
  æ (ash)    — represents /æ/ as in 'cat'
  ƿ (wynn)   — represents /w/ (normalized editions typically use 'w' instead)

Long vowels are conventionally marked with macrons in modern scholarly editions:
  ā, ē, ī, ō, ū

Scholarly standard: Klaeber's Beowulf, 4th edition (Klaeber 4), ed. Fulk,
Bjork, and Niles (University of Toronto Press, 2008).
"""

import re
import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language

# Characters that distinguish OE from modern English
OE_SPECIAL_CHARS = frozenset("þðæƿÞÐÆƿāēīōūĀĒĪŌŪ")

# Macron vowels mapping (long to short for normalization)
_MACRON_MAP = str.maketrans(
    "āēīōūĀĒĪŌŪ",
    "aeiouAEIOU",
)

# Transliteration table: OE character → approximate phonetic representation
_TRANSLIT_MAP = str.maketrans(
    {
        "þ": "th",
        "Þ": "Th",
        "ð": "th",
        "Ð": "Th",
        "æ": "ae",
        "Æ": "Ae",
        "ƿ": "w",
        "Ƿ": "W",
        "ā": "a",
        "ē": "e",
        "ī": "i",
        "ō": "o",
        "ū": "u",
        "Ā": "A",
        "Ē": "E",
        "Ī": "I",
        "Ō": "O",
        "Ū": "U",
    }
)


class OldEnglishModule(LanguageModule):
    @property
    def code(self) -> str:
        return "ang"

    @property
    def name(self) -> str:
        return "Old English"

    @property
    def script(self) -> str:
        return "Latin (with runic characters þ, ð, æ)"

    def normalize(self, text: str) -> str:
        """Normalize OE text for loose comparison.

        - Remove macrons from long vowels (ā → a, etc.)
        - Map þ and ð both to 'th'
        - Map æ to 'ae', ƿ to 'w'
        - Lowercase the result
        - Strip leading/trailing whitespace

        This allows matching across different editorial conventions (e.g., a text
        using macrons vs. one without, or þ vs. ð for the same sound).
        """
        # First strip macrons
        result = text.translate(_MACRON_MAP)
        # Then map OE special chars
        result = result.translate(_TRANSLIT_MAP)
        # Normalize any remaining Unicode (e.g., combining diacritics)
        result = unicodedata.normalize("NFC", result)
        return result.lower().strip()

    def transliterate(self, text: str) -> str:
        """Produce a rough pronunciation guide for Old English text.

        Maps OE special characters to their approximate modern phonetic
        equivalents using Latin letters:
          þ, ð  → th
          æ     → ae
          ƿ     → w
          macron vowels → plain vowels (length unmarked)

        This is intended as a reading aid, not a full IPA transcription.
        For serious phonological study, consult Hogg's Grammar of Old English
        (Blackwell, 1992) or Campbell's Old English Grammar (Oxford, 1959).
        """
        return text.translate(_TRANSLIT_MAP)

    def parse_morphology(self, word: str) -> dict[str, str] | None:
        """Basic morphological hints for common OE endings.

        Returns a dict with 'pos' (part of speech) and 'notes' if recognizable,
        otherwise None.  This is a stub — full OE morphological parsing requires
        a dedicated lexicon (e.g., the Dictionary of Old English Web Corpus).
        """
        w = self.normalize(word)

        # Very coarse heuristics based on common endings
        if w.endswith(("an", "ian")):
            return {"pos": "verb (infinitive)", "notes": "weak or strong infinitive ending"}
        if w.endswith(("um",)):
            return {"pos": "noun/adj (dative plural)", "notes": "dative plural -um"}
        if w.endswith(("as",)):
            return {"pos": "noun (nom/acc plural)", "notes": "strong masculine plural"}
        if w.endswith(("es",)):
            return {"pos": "noun (gen singular)", "notes": "strong masculine/neuter genitive"}
        if w.endswith(("en",)):
            return {"pos": "adj/participle", "notes": "weak adjective or past participle"}

        return None


old_english = OldEnglishModule()
register_language(old_english)
