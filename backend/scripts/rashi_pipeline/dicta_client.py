"""
Async Dicta morphological analysis client.

API: POST https://nakdan.dicta.org.il/api
Docs: https://dicta.org.il/tools/nakdan

We use genre="rabbinic" which activates Dicta's rabbinic Hebrew model —
critical for Rashi's Mishnaic Hebrew and Aramaic.

Rate limiting: Dicta's public API has no published rate limit, but
we apply conservative throttling (1 req/sec, batch size ≤ 500 chars)
to avoid hammering their servers.

Response format (per token):
{
  "word": "original token",
  "options": [
    {
      "nakdan": "vocalized form",
      "morph": "VQP3MS",
      "lemma": "אמר",
      "score": 0.95,
      "lex": "אמר"   // sometimes present
    },
    ...
  ]
}
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

DICTA_URL = "https://nakdan.dicta.org.il/api"
BATCH_CHAR_LIMIT = 500     # max chars per API request
MIN_CONFIDENCE_THRESHOLD = 0.6  # below this → flag uncertain
TOP_N_ALTERNATIVES = 3     # how many alternative analyses to store


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


class DictaClient:
    def __init__(self, requests_per_second: float = 1.0) -> None:
        self._delay = 1.0 / requests_per_second
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0

    async def __aenter__(self) -> "DictaClient":
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def _throttle(self) -> None:
        import time
        now = time.monotonic()
        wait = self._delay - (now - self._last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = time.monotonic()

    async def analyze_text(
        self, text: str, genre: str = "rabbinic", retries: int = 3
    ) -> list[DictaToken]:
        """
        Send a text batch to Dicta and return per-token analyses.
        genre: "rabbinic" | "biblical" | "modern" | "mixed"
        """
        assert self._client is not None, "Use as async context manager"

        await self._throttle()

        payload = {
            "task": "nakdan",
            "genre": genre,
            "data": text,
            "addmorph": True,
            "keepnikud": True,
            "keepqq": False,
        }

        for attempt in range(retries):
            try:
                resp = await self._client.post(DICTA_URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return [
                    DictaToken(word=item.get("word", ""), options=item.get("options", []))
                    for item in data
                ]
            except httpx.HTTPStatusError as e:
                logger.warning(f"Dicta HTTP error {e.response.status_code} (attempt {attempt+1})")
                if e.response.status_code in (429, 503) and attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.RequestError as e:
                logger.warning(f"Dicta request error: {e} (attempt {attempt+1})")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        return []


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
