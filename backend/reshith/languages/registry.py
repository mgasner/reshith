"""Registry for language modules."""

from reshith.languages.base import LanguageModule

_registry: dict[str, LanguageModule] = {}


def register_language(module: LanguageModule) -> None:
    """Register a language module."""
    _registry[module.code] = module


def get_language_module(code: str) -> LanguageModule | None:
    """Get a language module by its code."""
    return _registry.get(code)


def list_languages() -> list[LanguageModule]:
    """List all registered language modules."""
    return list(_registry.values())
