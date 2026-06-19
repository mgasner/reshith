"""LLM service for translation drills and language assistance."""

import json

from reshith.services.llm_providers import (
    DEFAULT_MODELS,
    LLMProvider,
    chat_complete,
)
from reshith.services.reference import format_for_prompt, search_gesenius

TRANSLATION_SYSTEM_PROMPT = """\
You are an expert tutor for classical languages, specializing in helping students \
develop reading and translation skills. You provide:

1. Accurate translations with grammatical explanations
2. Parsing of verb forms, noun declensions, and other morphology
3. Contextual notes about idioms, syntax, and usage
4. References to standard grammars when helpful, citing GKC section numbers (e.g. GKC §47)

Be concise but thorough. Focus on helping the student understand the underlying \
grammar and patterns."""


_NOT_CONFIGURED_MSG = (
    "LLM service not configured. Add an API key in Settings, or set "
    "OPENAI_API_KEY / ANTHROPIC_API_KEY on the server."
)


async def get_translation_help(
    text: str,
    language: str,
    context: str | None = None,
    *,
    provider: LLMProvider = LLMProvider.OPENAI,
    api_key: str | None = None,
    model: str | None = None,
    # Gesenius RAG only works against OpenAI embeddings; pass through
    # explicitly so we can keep using the env-level OpenAI key for the
    # embedding step even when the chat call goes to Anthropic.
    embedding_api_key: str | None = None,
) -> str:
    """Get LLM assistance for translating a text."""
    if not api_key:
        return _NOT_CONFIGURED_MSG

    user_prompt = f"Language: {language}\n\nText to translate:\n{text}"
    if context:
        user_prompt += f"\n\nContext: {context}"

    # Retrieve relevant GKC sections for Hebrew queries
    gkc_context = ""
    if language.lower() in ("biblical hebrew", "hebrew", "hbo"):
        chunks = await search_gesenius(
            text, top_k=3, api_key=embedding_api_key or api_key
        )
        gkc_context = format_for_prompt(chunks)

    messages: list[dict] = [{"role": "system", "content": TRANSLATION_SYSTEM_PROMPT}]
    if gkc_context:
        messages.append({"role": "system", "content": gkc_context})
    messages.append({"role": "user", "content": user_prompt})

    return await chat_complete(
        provider=provider,
        api_key=api_key,
        model=model or DEFAULT_MODELS[provider],
        messages=messages,
        temperature=0.3,
    )


async def generate_drill(
    vocabulary: list[str],
    language: str,
    difficulty: str = "intermediate",
    *,
    provider: LLMProvider = LLMProvider.OPENAI,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, str]:
    """Generate a translation drill using given vocabulary."""
    if not api_key:
        return {"error": _NOT_CONFIGURED_MSG}

    vocab_str = ", ".join(vocabulary)
    prompt = f"""Create a short translation exercise in {language} using these words: {vocab_str}

Difficulty level: {difficulty}

Provide:
1. A sentence or short passage in {language}
2. The English translation
3. Brief grammatical notes

Format as JSON with keys: "text", "translation", "notes"
"""

    raw = await chat_complete(
        provider=provider,
        api_key=api_key,
        model=model or DEFAULT_MODELS[provider],
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        json_mode=True,
    )

    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"error": "Model returned non-JSON response", "text": raw}
