"""Provider-agnostic LLM client abstraction.

The codebase needs OpenAI for embedding-based RAG (Gesenius semantic search)
and either OpenAI or Anthropic for chat completions. To keep call sites
small, this module exposes a single :func:`chat_complete` entry point that
dispatches by provider, and a :class:`LLMProvider` enum that flows through
the GraphQL surface unchanged.
"""

from __future__ import annotations

import enum
import json


class LLMProvider(enum.StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# Default model per provider — used when a model isn't passed explicitly
# (e.g. the exercise generators don't care which chat model is in use).
DEFAULT_MODELS: dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "gpt-4o",
    LLMProvider.ANTHROPIC: "claude-sonnet-4-5",
}


def normalize_provider(value: str | LLMProvider | None) -> LLMProvider:
    """Coerce a string/enum/None to a valid :class:`LLMProvider`.

    Unknown strings fall back to OpenAI so a typo in env config doesn't
    take the whole LLM surface offline.
    """
    if value is None:
        return LLMProvider.OPENAI
    if isinstance(value, LLMProvider):
        return value
    try:
        return LLMProvider(value.lower())
    except ValueError:
        return LLMProvider.OPENAI


async def chat_complete(
    *,
    provider: LLMProvider,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    """Run a chat completion against the chosen provider and return the text.

    ``messages`` uses the OpenAI shape — ``[{"role": "system"|"user"|"assistant",
    "content": "..."}]`` — and is translated to the Anthropic shape internally.
    """
    if provider == LLMProvider.ANTHROPIC:
        return await _anthropic_chat(
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=temperature,
            json_mode=json_mode,
        )
    return await _openai_chat(
        api_key=api_key,
        model=model,
        messages=messages,
        temperature=temperature,
        json_mode=json_mode,
    )


async def _openai_chat(
    *,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float,
    json_mode: bool,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def _anthropic_chat(
    *,
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float,
    json_mode: bool,
) -> str:
    from anthropic import AsyncAnthropic

    # Anthropic takes the system prompt as a separate field and only accepts
    # user/assistant roles in the messages array. Concatenate any system
    # messages and translate the rest.
    system_parts: list[str] = []
    converted: list[dict] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
        elif role in ("user", "assistant"):
            converted.append({"role": role, "content": content})

    if json_mode:
        # Anthropic has no native JSON mode — nudge the model and parse
        # defensively. The OpenAI-shaped callers already pass json.loads on
        # the result, so they handle the parsing themselves.
        system_parts.append(
            "Respond with a single valid JSON object only. Do not wrap the "
            "JSON in markdown code fences or include any prose."
        )

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=temperature,
        system="\n\n".join(system_parts) if system_parts else "",
        messages=converted,
    )

    # Anthropic returns a list of content blocks; concatenate the text ones.
    text_parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    text = "".join(text_parts)

    if json_mode:
        # Strip ```json fences if the model emitted them anyway, and validate.
        text = _strip_json_fences(text)
        try:
            json.loads(text)
        except json.JSONDecodeError:
            # Caller will see a parse error rather than silently using broken
            # output. Return the raw text so error messages stay informative.
            pass

    return text


def _strip_json_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop the opening fence (``` or ```json) and the closing fence.
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        if stripped.endswith("```"):
            stripped = stripped[: -3]
        stripped = stripped.strip()
    return stripped
