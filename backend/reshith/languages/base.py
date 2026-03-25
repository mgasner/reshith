"""Base class for language-specific modules."""

from abc import ABC, abstractmethod

CANTILLATION_RANGE = range(0x0591, 0x05AF + 1)


class LanguageModule(ABC):
    """Abstract base class for language-specific functionality."""

    @property
    @abstractmethod
    def code(self) -> str:
        """ISO 639-3 language code."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable language name."""
        ...

    @property
    @abstractmethod
    def script(self) -> str:
        """Primary script used (e.g., 'Hebrew', 'Latin', 'Devanagari')."""
        ...

    @property
    def rtl(self) -> bool:
        """Whether the language is written right-to-left."""
        return False

    @abstractmethod
    def transliterate(self, text: str) -> str:
        """Convert native script to Latin transliteration."""
        ...

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize text (remove cantillation marks, standardize forms, etc.)."""
        ...

    def parse_morphology(self, word: str) -> dict[str, str] | None:
        """Parse morphological information for a word. Override in subclasses."""
        return None
