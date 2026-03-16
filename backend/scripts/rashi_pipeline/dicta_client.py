"""
Async Dicta morphological analysis client with token-level disk cache.

API: POST https://nakdan.dicta.org.il/api
Docs: https://dicta.org.il/tools/nakdan

We use genre="rabbinic" which activates Dicta's rabbinic Hebrew model —
critical for Rashi's Mishnaic Hebrew and Aramaic.

Caching strategy:
- Each token is cached independently by its normalized form (no nikud/cantillation).
- The same Hebrew word (e.g. אמר) appears thousands of times across 36 books;
  caching at the token level avoids re-calling the API for duplicates.
- Cache location: CACHE_DIR/dicta_tokens/{hex_key}.json
- Cache format: the raw "options" list from the API (or [] for unrecognized).
- Before batching, uncached tokens are filtered out; results are merged back
  in original order.

Rate limiting: 1 req/sec default. Only applied to actual API calls — cache
hits are free and instantaneous.

Note on context-sensitivity: Dicta's API uses some inter-word context for
disambiguation. By caching per-token (out of context), we accept a small
accuracy tradeoff in exchange for a large reduction in API calls. The
uncertainty-flagging system catches genuinely ambiguous cases regardless.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from .tokenizer import strip_vowels

logger = logging.getLogger(__name__)

DICTA_URL = "https://nakdan.dicta.org.il/api"
BATCH_CHAR_LIMIT = 500     # max chars per API request
MIN_CONFIDENCE_THRESHOLD = 0.6  # below this → flag uncertain
TOP_N_ALTERNATIVES = 3     # how many alternative analyses to store

# Sentinel: a cached token that the API returned no options for
_EMPTY_OPTIONS: list = []


@dataclass
class DictaToken:
    word: str
    options: list[dict]   # raw option dicts from the API

    @property
    def best(self) -> dict | None:
        if not self.options:
            return None
        return max(self.options, key=lambda o: o.get("score", 0))

    @property
    def confidence(self) -> float:
        b = self.best
        if b is None:
            return 0.0
        return float(b.get("score", 0))

    @property
    def lemma(self) -> str | None:
        b = self.best
        if b is None:
            return None
        return b.get("lemma") or b.get("lex")

    @property
    def morph_code(self) -> str | None:
        b = self.best
        if b is None:
            return None
        return b.get("morph")

    @property
    def vocalized(self) -> str | None:
        b = self.best
        if b is None:
            return None
        return b.get("nakdan")

    @property
    def is_uncertain(self) -> bool:
        return self.confidence < MIN_CONFIDENCE_THRESHOLD

    @property
    def has_multiple_analyses(self) -> bool:
        if len(self.options) < 2:
            return False
        scores = sorted([o.get("score", 0) for o in self.options], reverse=True)
        # Flag if top two options are within 5% of each other
        return len(scores) >= 2 and (scores[0] - scores[1]) < 0.05

    def top_alternatives(self, n: int = TOP_N_ALTERNATIVES) -> list[dict]:
        """Return top-N alternatives (excluding the best) for display."""
        sorted_opts = sorted(self.options, key=lambda o: o.get("score", 0), reverse=True)
        return [
            {
                "vocalized": o.get("nakdan"),
                "morph": o.get("morph"),
                "lemma": o.get("lemma") or o.get("lex"),
                "score": round(float(o.get("score", 0)), 4),
            }
            for o in sorted_opts[1:n + 1]
        ]


class TokenCache:
    """
    Disk-backed cache for individual token analyses.
    Key: normalized token (strip_vowels applied).
    Value: raw options list from Dicta, or [] for "no analysis".
    A missing file means "not yet queried".
    """

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir / "dicta_tokens"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, list[dict] | None] = {}

    def _path(self, norm: str) -> Path:
        key = norm.encode("utf-8").hex()
        return self._dir / key[:2] / f"{key}.json"

    def get(self, surface: str) -> list[dict] | None:
        """
        Return cached options list, or None if not cached.
        (An empty list [] means "was queried, got no results" — distinct from None.)
        """
        norm = strip_vowels(surface)
        if norm in self._memory:
            return self._memory[norm]
        path = self._path(norm)
        if not path.exists():
            return None
        try:
            options = json.loads(path.read_text(encoding="utf-8"))
            self._memory[norm] = options
            return options
        except Exception:
            return None

    def set(self, surface: str, options: list[dict]) -> None:
        norm = strip_vowels(surface)
        path = self._path(norm)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(options, ensure_ascii=False), encoding="utf-8")
        self._memory[norm] = options

    def stats(self) -> tuple[int, int]:
        """Return (memory_hits, disk_files) for diagnostics."""
        disk = sum(1 for _ in self._dir.rglob("*.json"))
        return len(self._memory), disk


class DictaClient:
    def __init__(self, cache_dir: Path, requests_per_second: float = 1.0) -> None:
        self._delay = 1.0 / requests_per_second
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        self._cache = TokenCache(cache_dir)
        self._stats = {"cache_hits": 0, "api_calls": 0, "tokens_sent": 0}

    async def __aenter__(self) -> "DictaClient":
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()
        mem, disk = self._cache.stats()
        logger.info(
            f"Dicta cache stats — hits: {self._stats['cache_hits']}, "
            f"api_calls: {self._stats['api_calls']}, "
            f"tokens_sent: {self._stats['tokens_sent']}, "
            f"disk_entries: {disk}"
        )

    async def _throttle(self) -> None:
        now = time.monotonic()
        wait = self._delay - (now - self._last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = time.monotonic()

    async def _fetch_batch(self, tokens: list[str], genre: str, retries: int) -> list[DictaToken]:
        """Send a single batch to the API. Tokens must all be cache misses."""
        assert self._client is not None
        await self._throttle()

        text = " ".join(tokens)
        payload = {
            "task": "nakdan",
            "genre": genre,
            "data": text,
            "addmorph": True,
            "keepnikud": True,
            "keepqq": False,
        }

        self._stats["api_calls"] += 1
        self._stats["tokens_sent"] += len(tokens)

        for attempt in range(retries):
            try:
                resp = await self._client.post(DICTA_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
                results = [
                    DictaToken(word=item.get("word", ""), options=item.get("options", []))
                    for item in data
                ]
                # Cache each result. Align by position; Dicta may return fewer tokens
                # than we sent if it merges some — store what we can.
                for i, token in enumerate(tokens):
                    if i < len(results):
                        self._cache.set(token, results[i].options)
                    else:
                        # API returned fewer tokens than sent — mark remainder as unrecognized
                        self._cache.set(token, [])
                return results
            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                logger.warning(f"Dicta HTTP {code} (attempt {attempt + 1}/{retries})")
                if code in (429, 503) and attempt < retries - 1:
                    backoff = 2 ** attempt * 3
                    logger.info(f"  backing off {backoff}s")
                    await asyncio.sleep(backoff)
                    continue
                raise
            except httpx.RequestError as e:
                logger.warning(f"Dicta request error: {e} (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        return []

    async def analyze_tokens(
        self, tokens: list[str], genre: str = "rabbinic", retries: int = 3
    ) -> list[DictaToken]:
        """
        Analyze a list of tokens, serving cached results where available
        and batching only cache misses for API calls.

        Returns results in the same order as the input tokens list.
        """
        # Partition into cached vs. uncached
        results: dict[int, DictaToken] = {}
        uncached_indices: list[int] = []
        uncached_tokens: list[str] = []

        for i, token in enumerate(tokens):
            cached = self._cache.get(token)
            if cached is not None:
                self._stats["cache_hits"] += 1
                results[i] = DictaToken(word=token, options=cached)
            else:
                uncached_indices.append(i)
                uncached_tokens.append(token)

        if uncached_tokens:
            logger.debug(
                f"Dicta: {len(results)} cache hits, {len(uncached_tokens)} to fetch"
            )
            # Batch and fetch only uncached tokens
            batches = split_into_batches(uncached_tokens)
            batch_start = 0
            for batch in batches:
                try:
                    batch_results = await self._fetch_batch(batch, genre, retries)
                    for j, dt in enumerate(batch_results):
                        original_idx = uncached_indices[batch_start + j]
                        results[original_idx] = dt
                    # Fill any unmatched indices (API returned fewer tokens)
                    for j in range(len(batch_results), len(batch)):
                        original_idx = uncached_indices[batch_start + j]
                        results[original_idx] = DictaToken(word=batch[j], options=[])
                except Exception as e:
                    logger.error(f"Dicta batch failed: {e}")
                    for j in range(len(batch)):
                        original_idx = uncached_indices[batch_start + j]
                        results[original_idx] = DictaToken(word=batch[j], options=[])
                batch_start += len(batch)

        return [results[i] for i in range(len(tokens))]


def split_into_batches(tokens: list[str], char_limit: int = BATCH_CHAR_LIMIT) -> list[list[str]]:
    """
    Group tokens into batches that fit within the char limit.
    Dicta tokenizes on whitespace, so we join with spaces.
    """
    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0

    for token in tokens:
        token_len = len(token) + 1  # +1 for the space
        if current and current_len + token_len > char_limit:
            batches.append(current)
            current = [token]
            current_len = token_len
        else:
            current.append(token)
            current_len += token_len

    if current:
        batches.append(current)

    return batches
