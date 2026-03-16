"""LLM service for translation drills and language assistance."""

from openai import AsyncOpenAI

from reshith.core.config import get_settings

settings = get_settings()

client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None


TRANSLATION_SYSTEM_PROMPT = """\
You are an expert tutor for classical languages, specializing in helping students \
develop reading and translation skills. You provide:

1. Accurate translations with grammatical explanations
2. Parsing of verb forms, noun declensions, and other morphology
3. Contextual notes about idioms, syntax, and usage
4. References to standard grammars when helpful

Be concise but thorough. Focus on helping the student understand the underlying \
grammar and patterns."""


async def get_translation_help(
    text: str,
    language: str,
    context: str | None = None,
) -> str:
    """Get LLM assistance for translating a text."""
    if not client:
        return "LLM service not configured. Please set OPENAI_API_KEY."

    user_prompt = f"Language: {language}\n\nText to translate:\n{text}"
    if context:
        user_prompt += f"\n\nContext: {context}"

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content or ""


async def generate_drill(
    vocabulary: list[str],
    language: str,
    difficulty: str = "intermediate",
) -> dict[str, str]:
    """Generate a translation drill using given vocabulary."""
    if not client:
        return {"error": "LLM service not configured"}

    vocab_str = ", ".join(vocabulary)
    prompt = f"""Create a short translation exercise in {language} using these words: {vocab_str}

Difficulty level: {difficulty}

Provide:
1. A sentence or short passage in {language}
2. The English translation
3. Brief grammatical notes

Format as JSON with keys: "text", "translation", "notes"
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    import json

    return json.loads(response.choices[0].message.content or "{}")
