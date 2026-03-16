"""
Async Dicta morphological analysis client with token-level disk cache.

Actual API endpoint (reverse-engineered from nakdan.dicta.org.il frontend):
  POST https://nakdan-u1-0.loadbalancer.dicta.org.il/api

Payload:
  {
    "task": "nakdan",
    "genre": "rabbinic",   # "modern" | "biblical" | "rabbinic"
    "data": "<text>",
    "etagim": true,
    "keepqq": false,
    "nodageshdefmem": false,
    "patachma": false,
    "useTokenization": true
  }

Response per token:
  {
    "word": "<original>",
    "sep": false,          # true for whitespace/punctuation separators
    "fconfident": true,    # false when the model is uncertain
    "fpasuk": false,
    "options": [
      [
        "<vocalized>",     # best vocalization (options[0] = most likely)
        [
          ["<morph_id>", "<lemma>", false],  # morph analyses for this vocalization
          ...
        ]
      ],
      ...                  # further alternative vocalizations
    ]
  }

Note on morph IDs: morphology is encoded as opaque 64-bit integers in Dicta's
internal scheme. Without Dicta's decoder table, we store the raw ID. Lemma and
vocalized form are directly readable. Confidence comes from `fconfident`.

Caching strategy:
  Each token is cached by its normalized form (no nikud) so the same Hebrew word
  is only sent to the API once across the entire corpus.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from .tokenizer import strip_vowels

logger = logging.getLogger(__name__)

DICTA_URL = "https://nakdan-u1-0.loadbalancer.dicta.org.il/api"
BATCH_CHAR_LIMIT = 500
TOP_N_ALTERNATIVES = 3


@dataclass
class DictaToken:
    word: str
    vocalized: str | None          # best vocalization (options[0][0])
    lemma: str | None              # lemma from first morph analysis of best option
    morph_id: str | None           # raw morph integer ID (for future decoding)
    confident: bool                # fconfident from API
    alternatives: list[dict[str, Any]] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        return 1.0 if self.confident else 0.3

    @property
    def is_uncertain(self) -> bool:
        return not self.confident

    @property
    def has_multiple_analyses(self) -> bool:
        return len(self.alternatives) >= 1

    @property
    def morph_code(self) -> str | None:
        return self.morph_id  # kept for compatibility with morph_parser

    def top_alternatives(self, n: int = TOP_N_ALTERNATIVES) -> list[dict[str, Any]]:
        return self.alternatives[:n]

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "vocalized": self.vocalized,
            "lemma": self.lemma,
            "morph_id": self.morph_id,
            "confident": self.confident,
            "alternatives": self.alternatives,
        }

    @classmethod
    def from_cache_dict(cls, word: str, d: dict[str, Any]) -> "DictaToken":
        return cls(
            word=word,
            vocalized=d.get("vocalized"),
            lemma=d.get("lemma"),
            morph_id=d.get("morph_id"),
            confident=d.get("confident", False),
            alternatives=d.get("alternatives", []),
        )


def _parse_response_token(item: dict[str, Any]) -> DictaToken | None:
    """Parse a single token object from the Dicta API response."""
    # Skip separators (spaces, punctuation the API split off)
    if item.get("sep"):
        return None

    word = item.get("word", "")
    options: list = item.get("options", [])
    confident: bool = item.get("fconfident", False)

    vocalized: str | None = None
    lemma: str | None = None
    morph_id: str | None = None
    alternatives: list[dict[str, Any]] = []

    if options:
        best = options[0]
        if isinstance(best, str):
            # Plain-string format (no addmorph): just vocalization, no lemma
            vocalized = best
            for alt_opt in options[1:TOP_N_ALTERNATIVES + 1]:
                if isinstance(alt_opt, str):
                    alternatives.append({"vocalized": alt_opt, "lemma": None, "morph_id": None})
        elif isinstance(best, list) and len(best) >= 1:
            # Nested format (addmorph=true): [vocalized, [[id, lemma, flag], ...]]
            vocalized = best[0]
            morph_list = best[1] if len(best) > 1 else []
            if morph_list and isinstance(morph_list[0], list):
                first_morph = morph_list[0]
                morph_id = str(first_morph[0]) if len(first_morph) > 0 else None
                lemma = str(first_morph[1]) if len(first_morph) > 1 else None

            for alt_opt in options[1:TOP_N_ALTERNATIVES + 1]:
                if isinstance(alt_opt, list) and len(alt_opt) >= 1:
                    alt_voc = alt_opt[0]
                    alt_morph_list = alt_opt[1] if len(alt_opt) > 1 else []
                    alt_lemma = None
                    alt_morph_id = None
                    if alt_morph_list and isinstance(alt_morph_list[0], list):
                        alt_morph_id = str(alt_morph_list[0][0]) if alt_morph_list[0] else None
                        alt_lemma = str(alt_morph_list[0][1]) if len(alt_morph_list[0]) > 1 else None
                    alternatives.append({
                        "vocalized": alt_voc,
                        "lemma": alt_lemma,
                        "morph_id": alt_morph_id,
                    })

    return DictaToken(
        word=word,
        vocalized=vocalized,
        lemma=lemma,
        morph_id=morph_id,
        confident=confident,
        alternatives=alternatives,
    )


class TokenCache:
    """
    Disk-backed cache for individual token analyses.
    Key: normalized token (strip_vowels applied).
    Value: serialized DictaToken fields, or {} for "no analysis".
    A missing file means "not yet queried".
    """

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir / "dicta_tokens"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._memory: dict[str, dict[str, Any] | None] = {}

    def _path(self, norm: str) -> Path:
        key = norm.encode("utf-8").hex()
        return self._dir / key[:2] / f"{key}.json"

    def get(self, surface: str) -> DictaToken | None:
        """Return cached DictaToken, or None if not cached."""
        norm = strip_vowels(surface)
        if norm in self._memory:
            d = self._memory[norm]
            return None if d is None else DictaToken.from_cache_dict(surface, d)
        path = self._path(norm)
        if not path.exists():
            return None
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            self._memory[norm] = d
            return None if d is None else DictaToken.from_cache_dict(surface, d)
        except Exception:
            return None

    def set(self, surface: str, token: DictaToken | None) -> None:
        norm = strip_vowels(surface)
        d = None if token is None else token.to_cache_dict()
        path = self._path(norm)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        self._memory[norm] = d

    def stats(self) -> tuple[int, int]:
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
        _, disk = self._cache.stats()
        logger.info(
            f"Dicta cache — hits: {self._stats['cache_hits']}, "
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

    async def _fetch_batch(
        self, tokens: list[str], genre: str, retries: int
    ) -> list[DictaToken]:
        """Send a batch of cache-miss tokens to the API."""
        assert self._client is not None
        await self._throttle()

        # addmorph + keepnikud: required to get the nested options format
        # that includes lemmas and morph IDs (vs. plain string options).
        # We send the surface forms (which have nikud in Rashi text).
        payload = {
            "task": "nakdan",
            "genre": genre,
            "data": " ".join(tokens),
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
                raw = resp.json()

                # Filter out separator tokens; align results to our input
                parsed = [_parse_response_token(item) for item in raw]
                results = [t for t in parsed if t is not None]

                # Cache and return
                for i, token_surface in enumerate(tokens):
                    result = results[i] if i < len(results) else None
                    self._cache.set(token_surface, result)

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
        Analyze tokens, serving cache hits and only fetching misses.
        Returns results in the same order as input.
        """
        results: dict[int, DictaToken] = {}
        uncached_indices: list[int] = []
        uncached_tokens: list[str] = []

        for i, token in enumerate(tokens):
            cached = self._cache.get(token)
            if cached is not None:
                self._stats["cache_hits"] += 1
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_tokens.append(token)

        if uncached_tokens:
            logger.debug(
                f"Dicta: {len(results)} cache hits, {len(uncached_tokens)} to fetch"
            )
            batches = split_into_batches(uncached_tokens)
            batch_start = 0
            for batch in batches:
                try:
                    batch_results = await self._fetch_batch(batch, genre, retries)
                    for j, dt in enumerate(batch_results):
                        original_idx = uncached_indices[batch_start + j]
                        results[original_idx] = dt
                    # Fill any gaps where API returned fewer tokens than sent
                    for j in range(len(batch_results), len(batch)):
                        original_idx = uncached_indices[batch_start + j]
                        empty = DictaToken(
                            word=batch[j], vocalized=None, lemma=None,
                            morph_id=None, confident=False,
                        )
                        self._cache.set(batch[j], empty)
                        results[original_idx] = empty
                except Exception as e:
                    logger.error(f"Dicta batch failed: {e}")
                    for j in range(len(batch)):
                        original_idx = uncached_indices[batch_start + j]
                        results[original_idx] = DictaToken(
                            word=batch[j], vocalized=None, lemma=None,
                            morph_id=None, confident=False,
                        )
                batch_start += len(batch)

        return [results[i] for i in range(len(tokens))]


def split_into_batches(tokens: list[str], char_limit: int = BATCH_CHAR_LIMIT) -> list[list[str]]:
    batches: list[list[str]] = []
    current: list[str] = []
    current_len = 0
    for token in tokens:
        token_len = len(token) + 1
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
