"""
Sefaria lexicon client for BDB and Jastrow dictionary lookups.

Sefaria's word API returns entries from multiple lexicons:
- BDB (Brown-Driver-Briggs) — Biblical Hebrew
- Jastrow — Talmudic Aramaic and Mishnaic Hebrew
- Klein — CEDHL (Comprehensive Etymological Dictionary of the Hebrew Language)
- Gesenius — Hebrew and Chaldee Lexicon (older)
- Levy — Wörterbuch über die Talmudim (Aramaic)

API: GET https://www.sefaria.org/api/words/{word}
Returns: list of { ref, parent_lexicon, headword, content, ... }

We cache responses to disk to avoid repeat lookups across pipeline runs.
Cache is keyed by normalized (no-nikud) lemma.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

import httpx

from .models import DictionaryEntry
from .tokenizer import strip_vowels

logger = logging.getLogger(__name__)

SEFARIA_WORDS_URL = "https://www.sefaria.org/api/words/{word}"

# Preferred lexicon priority: for Hebrew prefer BDB, for Aramaic prefer Jastrow
LEXICON_PRIORITY = [
    "BDB",       # Brown-Driver-Briggs (Biblical Hebrew)
    "Jastrow",   # Marcus Jastrow (Mishnaic/Talmudic)
    "Klein CEDHL",
    "Gesenius",
    "Levy",
]

LEXICON_DISPLAY = {
    "BDB": "bdb",
    "Jastrow": "jastrow",
    "Klein CEDHL": "klein",
    "Gesenius": "gesenius",
    "Levy": "levy",
}


def _extract_gloss(content: dict) -> str:
    """Extract the short gloss from a Sefaria lexicon entry's content dict."""
    # Different lexicons structure content differently
    if "short_definition" in content:
        return content["short_definition"]
    if "morphology" in content and "gloss" in content:
        return content["gloss"]
    if "senses" in content and content["senses"]:
        first = content["senses"][0]
        if isinstance(first, dict):
            return first.get("definition", "")[:200]
        return str(first)[:200]
    if "text" in content:
        return str(content["text"])[:200]
    return ""


def _extract_definition(content: dict) -> str | None:
    """Extract a fuller definition if available."""
    if "senses" in content and len(content["senses"]) > 1:
        parts = []
        for sense in content["senses"][:3]:
            if isinstance(sense, dict):
                d = sense.get("definition", "")
                if d:
                    parts.append(d)
        return " | ".join(parts) if parts else None
    return None


def _best_entry(entries: list[dict]) -> DictionaryEntry | None:
    """Select the best entry from Sefaria's list based on lexicon priority."""
    by_lexicon: dict[str, dict] = {}
    for entry in entries:
        lex = entry.get("parent_lexicon", "")
        if lex not in by_lexicon:
            by_lexicon[lex] = entry

    for preferred in LEXICON_PRIORITY:
        if preferred in by_lexicon:
            e = by_lexicon[preferred]
            content = e.get("content", {})
            gloss = _extract_gloss(content)
            if not gloss:
                continue
            source_key = LEXICON_DISPLAY.get(preferred, preferred.lower())
            headword = e.get("headword", "")
            # Build a Sefaria search URL for the headword
            url = f"https://www.sefaria.org/search?q={headword}&tab=lexicon"
            return DictionaryEntry(
                source=source_key,
                headword=headword,
                gloss=gloss,
                definition=_extract_definition(content),
                entry_url=url,
            )

    return None


class SefariaLexicon:
    """
    Async Sefaria word lookup with disk caching.
    Cache lives at cache_dir/sefaria_words/{normalized_lemma}.json
    """

    def __init__(self, cache_dir: Path, requests_per_second: float = 2.0) -> None:
        self._cache_dir = cache_dir / "sefaria_words"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._delay = 1.0 / requests_per_second
        self._client: httpx.AsyncClient | None = None
        self._last_request: float = 0.0
        # Serialise concurrent callers so throttle is race-free
        self._lock = asyncio.Lock()
        # In-memory cache for this session (checked before acquiring lock)
        self._memory: dict[str, DictionaryEntry | None] = {}

    async def __aenter__(self) -> "SefariaLexicon":
        self._client = httpx.AsyncClient(timeout=20.0)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    def _cache_path(self, normalized_lemma: str) -> Path:
        # Use first two chars as a subdirectory to avoid huge flat directories
        safe = normalized_lemma.encode("utf-8").hex()
        return self._cache_dir / safe[:2] / f"{safe}.json"

    def _read_cache(self, normalized_lemma: str) -> DictionaryEntry | None | bool:
        """
        Return:
          DictionaryEntry  — cached hit
          None             — cached miss (we looked it up before, got nothing)
          False            — not in cache
        """
        if normalized_lemma in self._memory:
            return self._memory[normalized_lemma]
        path = self._cache_path(normalized_lemma)
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data is None:
                result: DictionaryEntry | None = None
            else:
                result = DictionaryEntry(**data)
            self._memory[normalized_lemma] = result
            return result
        except Exception:
            return False

    def _write_cache(self, normalized_lemma: str, entry: DictionaryEntry | None) -> None:
        path = self._cache_path(normalized_lemma)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = None if entry is None else entry.__dict__
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self._memory[normalized_lemma] = entry

    async def _throttle(self) -> None:
        """Wait so that we don't exceed requests_per_second. Must be called under self._lock."""
        now = time.monotonic()
        wait = self._delay - (now - self._last_request)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_request = time.monotonic()

    async def lookup(self, lemma: str, retries: int = 3) -> DictionaryEntry | None:
        """
        Look up a lemma, using cache if available.

        Cache hits are returned immediately without acquiring the lock.
        Network calls are serialised through self._lock so that concurrent
        asyncio.gather callers don't race on _throttle or duplicate requests.
        """
        assert self._client is not None, "Use as async context manager"

        norm = strip_vowels(lemma)

        # Fast path: check in-memory cache before touching the lock
        if norm in self._memory:
            return self._memory[norm]

        # Serialise all cache-miss paths
        async with self._lock:
            # Re-check after acquiring lock — another coroutine may have populated it
            cached = self._read_cache(norm)
            if cached is not False:
                return cached  # type: ignore[return-value]

            await self._throttle()

            for attempt in range(retries):
                try:
                    url = SEFARIA_WORDS_URL.format(word=norm)
                    resp = await self._client.get(url, params={"lookup_ref": "", "nevuchadnezar": "1"})
                    if resp.status_code == 404:
                        self._write_cache(norm, None)
                        return None
                    resp.raise_for_status()
                    data = resp.json()
                    entries = data if isinstance(data, list) else data.get("entries", [])
                    entry = _best_entry(entries)
                    self._write_cache(norm, entry)
                    return entry
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt * 2)
                        continue
                    logger.warning(f"Sefaria error for {norm!r}: {e}")
                    break
                except httpx.RequestError as e:
                    logger.warning(f"Sefaria request error for {norm!r}: {e}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    break

        self._write_cache(norm, None)
        return None
