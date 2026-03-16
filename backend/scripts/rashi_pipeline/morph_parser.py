"""
Parse Dicta morphological codes into structured Morphology objects.

Dicta uses a compact code scheme. Examples:
  VQP3MS  = Verb, Qal, Perfect, 3rd person, Masculine, Singular
  VNI2FS  = Verb, Niphal, Imperfect, 2nd person, Feminine, Singular
  VPC1CP  = Verb, Piel, Participle, 1st person, Common, Plural
  NCmsa   = Noun, Common, masculine, singular, absolute
  NCfsc   = Noun, Common, feminine, singular, construct
  NCfsd   = Noun, Common, feminine, singular, determined (Aramaic)
  Sp      = Preposition
  Cc      = Conjunction, coordinative
  Cs      = Conjunction, subordinate
  Pd      = Pronoun, demonstrative
  Pp      = Pronoun, personal
  Pq      = Pronoun, interrogative
  Pr      = Pronoun, relative
  D       = Adverb
  T       = Particle

NOTE: Dicta's actual API format should be verified against live responses.
This parser is written against the documented format; if codes differ,
adjust the mapping tables below.
"""

from __future__ import annotations

from .models import Morphology

# Part-of-speech mapping (first character of code)
_POS_MAP: dict[str, str] = {
    "V": "verb",
    "N": "noun",
    "A": "adjective",
    "S": "preposition",
    "C": "conjunction",
    "P": "pronoun",
    "D": "adverb",
    "T": "particle",
    "R": "preposition",   # some schemes use R for preps
    "M": "numeral",
    "I": "interjection",
}

# Binyan codes (second char when POS=V)
_BINYAN_MAP: dict[str, str] = {
    "Q": "Qal",
    "N": "Niphal",
    "P": "Piel",
    "U": "Pual",
    "H": "Hiphil",
    "O": "Hophal",
    "T": "Hithpael",
    "D": "Piel",      # alternate encoding
    "E": "Pual",
    "L": "Piel",
    "M": "Poel",
    "Z": "Hithpoel",
    "G": "Qal passive",
}

# Tense/aspect codes (third char when POS=V)
_TENSE_MAP: dict[str, str] = {
    "P": "perfect",
    "I": "imperfect",
    "M": "imperative",
    "A": "infinitive absolute",
    "C": "infinitive construct",
    "R": "participle active",
    "S": "participle passive",
    "W": "wayyiqtol",  # consecutive imperfect
    "J": "jussive",
    "K": "cohortative",
}

# Person codes
_PERSON_MAP: dict[str, str] = {
    "1": "1", "2": "2", "3": "3",
}

# Gender codes
_GENDER_MAP: dict[str, str] = {
    "M": "m", "F": "f", "C": "c", "B": "c",
    "m": "m", "f": "f", "c": "c",
}

# Number codes
_NUMBER_MAP: dict[str, str] = {
    "S": "sg", "P": "pl", "D": "du",
    "s": "sg", "p": "pl", "d": "du",
}

# State codes (for nouns/adjectives)
_STATE_MAP: dict[str, str] = {
    "a": "absolute", "c": "construct", "d": "determined",
    "A": "absolute", "C": "construct", "D": "determined",
}


def parse_morph_code(code: str | None) -> Morphology:
    """
    Parse a Dicta morph code string into a Morphology dataclass.
    Unknown codes are stored in raw_code and pos is set to 'unknown'.
    """
    morph = Morphology(raw_code=code)

    if not code:
        return morph

    code = code.strip()
    if not code:
        return morph

    pos_char = code[0].upper()
    morph.pos = _POS_MAP.get(pos_char, "unknown")

    if morph.pos == "verb" and len(code) >= 2:
        morph.binyan = _BINYAN_MAP.get(code[1].upper())
        if len(code) >= 3:
            morph.tense = _TENSE_MAP.get(code[2].upper())
        if len(code) >= 4:
            morph.person = _PERSON_MAP.get(code[3])
        if len(code) >= 5:
            morph.gender = _GENDER_MAP.get(code[4])
        if len(code) >= 6:
            morph.number = _NUMBER_MAP.get(code[5])

    elif morph.pos in ("noun", "adjective") and len(code) >= 4:
        # NCgns where g=gender, n=number, s=state
        morph.gender = _GENDER_MAP.get(code[2])
        morph.number = _NUMBER_MAP.get(code[3])
        if len(code) >= 5:
            morph.state = _STATE_MAP.get(code[4])

    elif morph.pos == "pronoun" and len(code) >= 3:
        pronoun_type_map = {
            "d": "demonstrative", "p": "personal",
            "q": "interrogative", "r": "relative",
            "i": "indefinite",
        }
        morph.adjective_type = pronoun_type_map.get(code[1].lower(), "unknown")
        if len(code) >= 4:
            morph.person = _PERSON_MAP.get(code[2])
        if len(code) >= 5:
            morph.gender = _GENDER_MAP.get(code[3])
        if len(code) >= 6:
            morph.number = _NUMBER_MAP.get(code[4])

    return morph
