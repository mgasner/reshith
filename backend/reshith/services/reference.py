"""Reference search service for Gesenius' Hebrew Grammar (GKC).

The index file (data/references/gesenius_index.jsonl) is built by running:
    python scripts/build_gesenius_index.py

When embeddings are present, queries are answered with semantic (vector) search.
If the index has no embeddings yet, it falls back to simple keyword search so
the service is always usable.
"""

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "references"
INDEX_FILE = DATA_DIR / "gesenius_index.jsonl"

EMBEDDING_MODEL = "text-embedding-3-small"
# Chars of section text included in LLM context per result
CONTEXT_CHARS = 800


class ReferenceChunk(TypedDict):
    section: str
    title: str
    text: str
    score: float


# ---------------------------------------------------------------------------
# Index loading (cached for the process lifetime)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    records = []
    with INDEX_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _keyword_search(query: str, index: list[dict], top_k: int) -> list[ReferenceChunk]:
    words = set(re.findall(r"\w+", query.lower()))
    scored: list[tuple[int, dict]] = []
    for record in index:
        text_lower = record["text"].lower()
        score = sum(1 for w in words if w in text_lower)
        if score > 0:
            scored.append((score, record))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        ReferenceChunk(
            section=r["section"],
            title=r["title"],
            text=r["text"],
            score=float(s),
        )
        for s, r in scored[:top_k]
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search_gesenius(
    query: str,
    top_k: int = 3,
    api_key: str | None = None,
) -> list[ReferenceChunk]:
    """Return the top-k GKC sections most relevant to *query*.

    Uses semantic search when an embedding index exists; falls back to keyword
    search otherwise (or when no API key is available).
    """
    index = _load_index()
    if not index:
        return []

    has_embeddings = bool(index[0].get("embedding"))

    if not has_embeddings or not api_key:
        return _keyword_search(query, index, top_k)

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.embeddings.create(model=EMBEDDING_MODEL, input=query)
    query_vec = response.data[0].embedding

    scored = [(_cosine(query_vec, record["embedding"]), record) for record in index]
    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        ReferenceChunk(
            section=r["section"],
            title=r["title"],
            text=r["text"],
            score=s,
        )
        for s, r in scored[:top_k]
    ]


def format_for_prompt(chunks: list[ReferenceChunk]) -> str:
    """Render retrieved chunks as a block suitable for an LLM system/user prompt."""
    if not chunks:
        return ""
    lines = ["--- Gesenius' Hebrew Grammar (GKC) reference ---"]
    for chunk in chunks:
        lines.append(f"\n[GKC {chunk['section']} — {chunk['title']}]")
        lines.append(chunk["text"][:CONTEXT_CHARS])
    lines.append("--- end of GKC reference ---")
    return "\n".join(lines)
