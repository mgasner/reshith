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
    "No API key on file. Add an OpenAI or Anthropic API key in Settings to "
    "enable LLM-powered features."
)


async def get_translation_help(
    text: str,
    language: str,
    context: str | None = None,
    *,
    provider: LLMProvider = LLMProvider.OPENAI,
    api_key: str | None = None,
    model: str | None = None,
    # Gesenius RAG only works against OpenAI embeddings; pass an OpenAI key
    # explicitly so the embedding step can use the user's (or env-level)
    # OpenAI key even when the chat call goes to Anthropic. When this is
    # None and no OpenAI key is available, search_gesenius falls back to
    # keyword search.
    embedding_api_key: str | None = None,
) -> str:
    """Get LLM assistance for translating a text."""
    if not api_key:
        return _NOT_CONFIGURED_MSG

    user_prompt = f"Language: {language}\n\nText to translate:\n{text}"
    if context:
        user_prompt += f"\n\nContext: {context}"

    # Retrieve relevant GKC sections for Hebrew queries. Forward only an
    # OpenAI key — passing the chat api_key (which may be Anthropic) would
    # crash the OpenAI embeddings client. With no OpenAI key,
    # search_gesenius transparently degrades to keyword search.
    gkc_context = ""
    if language.lower() in ("biblical hebrew", "hebrew", "hbo"):
        chunks = await search_gesenius(text, top_k=3, api_key=embedding_api_key)
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
