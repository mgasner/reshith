"""Data models for the Rashi enrichment pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Language(StrEnum):
    HEBREW = "hebrew"
    ARAMAIC = "aramaic"
    OLD_FRENCH = "old_french"
    ABBREVIATION = "abbreviation"
    PUNCTUATION = "punctuation"
    UNKNOWN = "unknown"


class UncertaintyReason(StrEnum):
    LOW_CONFIDENCE = "low_confidence"         # Dicta score below threshold
    MULTIPLE_ANALYSES = "multiple_analyses"   # Dicta returned several equally-scored options
    ARAMAIC = "aramaic"                       # Token identified as Aramaic
    OLD_FRENCH = "old_french"                 # Token identified as Old French (laaz)
    ABBREVIATION = "abbreviation"             # Token is an abbreviation
    UNKNOWN_EXPANSION = "unknown_expansion"   # Abbreviation with no known expansion
    NO_DICTIONARY = "no_dictionary"           # No dictionary entry found
    UNRECOGNIZED = "unrecognized"             # Dicta could not analyze


@dataclass
class Morphology:
    pos: str | None = None            # noun, verb, prep, conj, adv, pron, particle, ...
    # Verb fields
    binyan: str | None = None         # Qal, Niphal, Piel, Pual, Hiphil, Hophal, Hithpael
    tense: str | None = None          # perfect, imperfect, imperative, infinitive, participle
    person: str | None = None         # 1, 2, 3
    gender: str | None = None         # m, f, c (common)
    number: str | None = None         # sg, pl, du
    # Noun/adjective fields
    state: str | None = None          # absolute, construct, determined
    # Verb participle / adjective
    adjective_type: str | None = None
    # Raw morph code from Dicta, for reference
    raw_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DictionaryEntry:
    source: str                        # "bdb", "jastrow", "custom_laaz", "custom_abbrev"
    headword: str
    gloss: str
    definition: str | None = None
    entry_url: str | None = None


@dataclass
class Token:
    # Surface form as it appears in the source text (may include vowel marks)
    surface: str
    # Normalized: strip vowels/cantillation for lookup purposes
    normalized: str
    language: Language
    # Was this token inside <b> tags (i.e. the biblical lemma being commented on)
    is_biblical_quote: bool = False
    # Lemma returned by the morphological analyzer
    lemma: str | None = None
    root: str | None = None
    morphology: Morphology | None = None
    # Prefixes split off before analysis (e.g. ו, ב, ל, כ, מ, ש, ה)
    prefixes: list[str] = field(default_factory=list)
    # Confidence score from Dicta (0.0–1.0)
    confidence: float | None = None
    # Whether this token's analysis should be treated with caution
    uncertain: bool = False
    uncertainty_reasons: list[UncertaintyReason] = field(default_factory=list)
    # All alternatives Dicta returned (for display/debugging)
    alternatives: list[dict[str, Any]] = field(default_factory=list)
    # Dictionary lookup result
    dictionary: DictionaryEntry | None = None
    # For abbreviations, the expanded form
    abbreviation_expansion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "surface": self.surface,
            "normalized": self.normalized,
            "language": self.language.value,
        }
        if self.is_biblical_quote:
            d["is_biblical_quote"] = True
        if self.lemma:
            d["lemma"] = self.lemma
        if self.root:
            d["root"] = self.root
        if self.morphology:
            d["morphology"] = self.morphology.to_dict()
        if self.prefixes:
            d["prefixes"] = self.prefixes
        if self.confidence is not None:
            d["confidence"] = round(self.confidence, 4)
        if self.uncertain:
            d["uncertain"] = True
            d["uncertainty_reasons"] = [r.value for r in self.uncertainty_reasons]
        if self.alternatives:
            d["alternatives"] = self.alternatives
        if self.dictionary:
            entry: dict[str, Any] = {
                "source": self.dictionary.source,
                "headword": self.dictionary.headword,
                "gloss": self.dictionary.gloss,
            }
            if self.dictionary.definition:
                entry["definition"] = self.dictionary.definition
            if self.dictionary.entry_url:
                entry["entry_url"] = self.dictionary.entry_url
            d["dictionary"] = entry
        if self.abbreviation_expansion:
            d["abbreviation_expansion"] = self.abbreviation_expansion
        return d


@dataclass
class EnrichedVerse:
    chapter: int
    verse: int
    tokens: list[Token]
    # Aggregate stats for quick filtering in the UI
    has_uncertain: bool = False
    has_old_french: bool = False
    has_aramaic: bool = False
    has_abbreviation: bool = False

    def compute_flags(self) -> None:
        for t in self.tokens:
            if t.uncertain:
                self.has_uncertain = True
            if t.language == Language.OLD_FRENCH:
                self.has_old_french = True
            if t.language == Language.ARAMAIC:
                self.has_aramaic = True
            if t.language == Language.ABBREVIATION:
                self.has_abbreviation = True

    def to_dict(self) -> dict[str, Any]:
        self.compute_flags()
        d: dict[str, Any] = {"tokens": [t.to_dict() for t in self.tokens]}
        for flag in ("has_uncertain", "has_old_french", "has_aramaic", "has_abbreviation"):
            if getattr(self, flag):
                d[flag] = True
        return d
