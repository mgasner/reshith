"""Unit tests for the LLM lemma/gloss assist feature.

Covers both the pure-function service layer (`reshith.services.llm.
suggest_lemma_gloss`) and the resolver gating logic
(`mutate_suggest_lemma_gloss`). Neither set of tests hits the network or
the database — the resolver tests inject a fake Strawberry ``info``
object and pre-populate ``info.context['user_api_keys_row']`` so the DB
lookup short-circuits.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from reshith.api import resolvers
from reshith.api.types import LanguageCode, SuggestLemmaGlossInput
from reshith.services import llm
from reshith.services.llm_providers import LLMProvider

# ── service layer ─────────────────────────────────────────────────────────────


async def test_suggest_lemma_gloss_no_api_key_short_circuits():
    """No network call is attempted when the user has no API key."""
    result = await llm.suggest_lemma_gloss(
        form="amor", language="Latin", api_key=None
    )
    assert "error" in result
    assert "API key" in result["error"]


async def test_suggest_lemma_gloss_parses_valid_json(monkeypatch):
    """Happy path: JSON keys are mirrored, missing keys collapse to None."""

    async def fake_chat_complete(**_kwargs):
        return (
            '{"lemma": "amor", "gloss": "love", '
            '"transliteration": null, "notes": "Latin noun"}'
        )

    monkeypatch.setattr(llm, "chat_complete", fake_chat_complete)
    result = await llm.suggest_lemma_gloss(
        form="amoris",
        language="Latin",
        lemma_hint="amor",
        context="In principio amoris...",
        api_key="sk-test",
    )
    assert result == {
        "lemma": "amor",
        "gloss": "love",
        "transliteration": None,
        "notes": "Latin noun",
    }


async def test_suggest_lemma_gloss_handles_missing_fields(monkeypatch):
    """Models that omit optional keys produce ``None`` rather than KeyError."""

    async def fake_chat_complete(**_kwargs):
        return '{"lemma": "amor"}'

    monkeypatch.setattr(llm, "chat_complete", fake_chat_complete)
    result = await llm.suggest_lemma_gloss(
        form="amoris", language="Latin", api_key="sk-test"
    )
    assert result == {
        "lemma": "amor",
        "gloss": None,
        "transliteration": None,
        "notes": None,
    }


async def test_suggest_lemma_gloss_handles_non_json(monkeypatch):
    """Non-JSON model output is returned as a structured error, not a crash."""

    async def fake_chat_complete(**_kwargs):
        return "I'm afraid I can't do that."

    monkeypatch.setattr(llm, "chat_complete", fake_chat_complete)
    result = await llm.suggest_lemma_gloss(
        form="amoris", language="Latin", api_key="sk-test"
    )
    assert "error" in result
    assert result.get("text") == "I'm afraid I can't do that."


# ── resolver gating ───────────────────────────────────────────────────────────


def _make_info(*, user_id=None, api_keys_row=None):
    """Construct a fake Strawberry ``Info`` for resolver tests.

    Pre-populates ``user_api_keys_row`` so ``_load_user_api_keys_row``
    short-circuits without touching the DB.
    """
    ctx: dict = {"current_user_id": user_id, "user_api_keys_row": api_keys_row}
    return SimpleNamespace(context=ctx)


def _api_keys_row(
    *,
    llm_lemma_assist: bool,
    anthropic_ciphertext: str | None = None,
    openai_ciphertext: str | None = None,
    preferred: str | None = "anthropic",
) -> SimpleNamespace:
    """Stand-in for the SQLAlchemy ``UserAPIKeys`` row."""
    return SimpleNamespace(
        llm_lemma_assist=llm_lemma_assist,
        anthropic_api_key_encrypted=anthropic_ciphertext,
        openai_api_key_encrypted=openai_ciphertext,
        preferred_provider=preferred,
    )


async def test_resolver_requires_authentication():
    info = _make_info(user_id=None)
    with pytest.raises(Exception, match="Not authenticated"):
        await resolvers.mutate_suggest_lemma_gloss(
            info,
            SuggestLemmaGlossInput(language=LanguageCode.LATIN, form="amor"),
        )


async def test_resolver_returns_unavailable_when_no_row():
    info = _make_info(user_id=uuid4(), api_keys_row=None)
    result = await resolvers.mutate_suggest_lemma_gloss(
        info,
        SuggestLemmaGlossInput(language=LanguageCode.LATIN, form="amor"),
    )
    assert result.available is False
    assert result.message and "Settings" in result.message


async def test_resolver_returns_unavailable_when_flag_off():
    info = _make_info(
        user_id=uuid4(),
        api_keys_row=_api_keys_row(
            llm_lemma_assist=False, anthropic_ciphertext="ciphertext"
        ),
    )
    result = await resolvers.mutate_suggest_lemma_gloss(
        info,
        SuggestLemmaGlossInput(language=LanguageCode.LATIN, form="amor"),
    )
    assert result.available is False
    assert result.lemma is None


async def test_resolver_returns_unavailable_when_no_key(monkeypatch):
    """Toggle on but no decryptable key → unavailable with helpful message."""
    monkeypatch.setattr(
        resolvers.secrets_crypto, "decrypt", lambda _ciphertext: None
    )
    info = _make_info(
        user_id=uuid4(),
        api_keys_row=_api_keys_row(
            llm_lemma_assist=True,
            anthropic_ciphertext="ciphertext",
        ),
    )
    result = await resolvers.mutate_suggest_lemma_gloss(
        info,
        SuggestLemmaGlossInput(language=LanguageCode.LATIN, form="amor"),
    )
    assert result.available is False
    assert "API key" in (result.message or "")


async def test_resolver_calls_llm_when_enabled(monkeypatch):
    """When toggle on and key present, the LLM is called and result returned."""
    monkeypatch.setattr(
        resolvers.secrets_crypto, "decrypt", lambda _ciphertext: "sk-fake"
    )
    called: dict = {}

    async def fake_suggest(*, form, language, lemma_hint, context, provider, api_key, model):
        called.update(
            form=form,
            language=language,
            lemma_hint=lemma_hint,
            context=context,
            provider=provider,
            api_key=api_key,
            model=model,
        )
        return {
            "lemma": "amor",
            "gloss": "love",
            "transliteration": None,
            "notes": None,
        }

    monkeypatch.setattr(resolvers.llm, "suggest_lemma_gloss", fake_suggest)

    info = _make_info(
        user_id=uuid4(),
        api_keys_row=_api_keys_row(
            llm_lemma_assist=True,
            anthropic_ciphertext="ciphertext",
            preferred="anthropic",
        ),
    )
    result = await resolvers.mutate_suggest_lemma_gloss(
        info,
        SuggestLemmaGlossInput(
            language=LanguageCode.LATIN,
            form="amoris",
            lemma_hint="amor",
            context="In principio amoris...",
        ),
    )
    assert result.available is True
    assert result.lemma == "amor"
    assert result.gloss == "love"
    # The full human-readable language label flows through, not the enum code.
    assert called["language"] == "Latin"
    assert called["form"] == "amoris"
    assert called["lemma_hint"] == "amor"
    assert called["api_key"] == "sk-fake"
    assert called["provider"] == LLMProvider.ANTHROPIC


async def test_resolver_propagates_service_error_as_unavailable(monkeypatch):
    """Service-layer errors (bad JSON, network) surface as availability=False."""
    monkeypatch.setattr(
        resolvers.secrets_crypto, "decrypt", lambda _ciphertext: "sk-fake"
    )

    async def fake_suggest(**_kwargs):
        return {"error": "Model returned non-JSON response", "text": "..."}

    monkeypatch.setattr(resolvers.llm, "suggest_lemma_gloss", fake_suggest)

    info = _make_info(
        user_id=uuid4(),
        api_keys_row=_api_keys_row(
            llm_lemma_assist=True, anthropic_ciphertext="ciphertext"
        ),
    )
    result = await resolvers.mutate_suggest_lemma_gloss(
        info,
        SuggestLemmaGlossInput(language=LanguageCode.LATIN, form="amor"),
    )
    assert result.available is False
    assert result.message and "non-JSON" in result.message
