"""Tests for the LLM provider abstraction (pure transforms, no network)."""

import pytest

from reshith.services.llm_providers import (
    DEFAULT_MODELS,
    LLMProvider,
    _strip_json_fences,
    normalize_provider,
)


def test_normalize_provider_known_strings():
    assert normalize_provider("openai") == LLMProvider.OPENAI
    assert normalize_provider("ANTHROPIC") == LLMProvider.ANTHROPIC


def test_normalize_provider_falls_back_to_openai():
    # Typos in env config shouldn't take the whole LLM surface offline.
    assert normalize_provider(None) == LLMProvider.OPENAI
    assert normalize_provider("not-a-real-provider") == LLMProvider.OPENAI


def test_default_models_cover_every_provider():
    for provider in LLMProvider:
        assert provider in DEFAULT_MODELS
        assert DEFAULT_MODELS[provider]


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('   ```json\n{"a": 1}\n```   ', '{"a": 1}'),
    ],
)
def test_strip_json_fences_handles_anthropic_quirks(raw, expected):
    assert _strip_json_fences(raw) == expected
