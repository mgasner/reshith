"""Biblical Hebrew language module."""

import unicodedata

from reshith.languages.base import LanguageModule
from reshith.languages.registry import register_language

HEBREW_TO_LATIN = {
    "א": "ʾ",
    "ב": "b",
    "ג": "g",
    "ד": "d",
    "ה": "h",
    "ו": "w",
    "ז": "z",
    "ח": "ḥ",
    "ט": "ṭ",
    "י": "y",
    "כ": "k",
    "ך": "k",
    "ל": "l",
    "מ": "m",
    "ם": "m",
    "נ": "n",
    "ן": "n",
    "ס": "s",
    "ע": "ʿ",
    "פ": "p",
    "ף": "p",
    "צ": "ṣ",
    "ץ": "ṣ",
    "ק": "q",
    "ר": "r",
    "שׁ": "š",
    "שׂ": "ś",
    "ש": "š",
    "ת": "t",
}

CANTILLATION_RANGE = range(0x0591, 0x05AF + 1)
POINTS_RANGE = range(0x05B0, 0x05BD + 1)
SHIN_SIN_DOT = {0x05C1, 0x05C2}


class BiblicalHebrewModule(LanguageModule):
    @property
    def code(self) -> str:
        return "hbo"

    @property
    def name(self) -> str:
        return "Biblical Hebrew"

    @property
    def script(self) -> str:
        return "Hebrew"

    @property
    def rtl(self) -> bool:
        return True

    def transliterate(self, text: str) -> str:
        result = []
        for char in text:
            if char in HEBREW_TO_LATIN:
                result.append(HEBREW_TO_LATIN[char])
            elif ord(char) not in CANTILLATION_RANGE and ord(char) not in POINTS_RANGE:
                result.append(char)
        return "".join(result)

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        result = []
        for char in text:
            code = ord(char)
            if code not in CANTILLATION_RANGE:
                result.append(char)
        return "".join(result)

    def strip_vowels(self, text: str) -> str:
        result = []
        for char in text:
            code = ord(char)
            if (
                code not in CANTILLATION_RANGE
                and code not in POINTS_RANGE
                and code not in SHIN_SIN_DOT
            ):
                result.append(char)
        return "".join(result)

    def parse_morphology(self, word: str) -> dict[str, str] | None:
        return None


biblical_hebrew = BiblicalHebrewModule()
register_language(biblical_hebrew)
