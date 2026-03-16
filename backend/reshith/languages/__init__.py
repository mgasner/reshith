"""Language-specific modules for different classical languages."""

from reshith.languages.base import LanguageModule
from reshith.languages.registry import get_language_module, register_language

__all__ = ["LanguageModule", "get_language_module", "register_language"]
