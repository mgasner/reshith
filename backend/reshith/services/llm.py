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


LEMMA_ASSIST_SYSTEM_PROMPT = """\
You are a lexicographer producing flashcard entries for a classical-languages \
student. Given a surface form pulled from a sacred or classical text, return \
JSON with the dictionary lemma, a short English gloss (≤8 words), an \
optional romanization, and an optional short note (etymology, register, or \
cross-reference). Never invent forms — if you're unsure, prefer leaving a \
field empty. Respond with JSON only."""


async def suggest_lemma_gloss(
    *,
    form: str,
    language: str,
    lemma_hint: str | None = None,
    context: str | None = None,
    provider: LLMProvider = LLMProvider.ANTHROPIC,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, str | None]:
    """Ask an LLM to fill in a card-quality lemma + gloss for a token.

    Returns ``{"error": ...}`` when no API key is configured; otherwise a
    dict with optional ``lemma``, ``gloss``, ``transliteration``, ``notes``
    keys. The caller decides which fields to merge into the card.
    """
    if not api_key:
        return {"error": _NOT_CONFIGURED_MSG}

    parts = [
        f"Language: {language}",
        f"Surface form: {form}",
    ]
    if lemma_hint:
        parts.append(f"Lemma hint from morphological analyzer: {lemma_hint}")
    if context:
        parts.append(f"Surrounding passage: {context}")
    parts.append(
        'Respond with a JSON object using these keys (omit a field by setting '
        'it to null): "lemma" (dictionary form), "gloss" (short English '
        'translation, ≤8 words), "transliteration" (romanization, if '
        'applicable), "notes" (one short usage note, optional).'
    )
    user_prompt = "\n".join(parts)

    raw = await chat_complete(
        provider=provider,
        api_key=api_key,
        model=model or DEFAULT_MODELS[provider],
        messages=[
            {"role": "system", "content": LEMMA_ASSIST_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        json_mode=True,
    )

    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"error": "Model returned non-JSON response", "text": raw}

    return {
        "lemma": parsed.get("lemma") or None,
        "gloss": parsed.get("gloss") or None,
        "transliteration": parsed.get("transliteration") or None,
        "notes": parsed.get("notes") or None,
    }
