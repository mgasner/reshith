#!/usr/bin/env python3
"""
Download Baal HaTurim commentary from Sefaria API and save as static JSON.

Output: frontend/public/data/hebrew/baal_haturim/{abbrev}.json
Format: { "chapter": { "verse": "html text", ... }, ... }  (1-based string keys)

Run from repo root:
  python data/hebrew/fetch_baal_haturim.py          # all books
  python data/hebrew/fetch_baal_haturim.py Gen Exo  # specific books

Notes:
  - All five books use the Kitzur (abridged) Baal HaTurim. Sefaria's "full"
    Baal HaTurim on Genesis has content in only 5 of 49 chapters; the Kitzur
    covers all 50 chapters comprehensively and is the consistent choice.
  - All five refs share the same depth-3 structure (Chapter.Verse.Comment), so
    the same range-fetch strategy used for Rashi applies here.
  - Many verses have zero comments (sparse); those are silently skipped.
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

SEFARIA_API = "https://www.sefaria.org/api/texts"
SEFARIA_SHAPE = "https://www.sefaria.org/api/shape"

BOOKS: dict[str, str] = {
    "Gen": "Kitzur_Ba'al_HaTurim_on_Genesis",
    "Exo": "Kitzur_Ba'al_HaTurim_on_Exodus",
    "Lev": "Kitzur_Ba'al_HaTurim_on_Leviticus",
    "Num": "Kitzur_Ba'al_HaTurim_on_Numbers",
    "Deu": "Kitzur_Ba'al_HaTurim_on_Deuteronomy",
}

OUTPUT_DIR = Path(__file__).parents[2] / "frontend" / "public" / "data" / "hebrew" / "baal_haturim"


def get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "reshith-baal-haturim-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def flatten(text: object) -> str:
    """Flatten a possibly-nested Sefaria segment list to a single HTML string."""
    if isinstance(text, str):
        return text.strip()
    if isinstance(text, list):
        return " ".join(flatten(t) for t in text if t).strip()
    return ""


def fetch_shape(ref: str) -> list:
    data = get(f"{SEFARIA_SHAPE}/{ref}")
    if isinstance(data, list) and data:
        return data[0].get("chapters", [])
    return []


def fetch_chapter(ref: str, chapter: int, verse_count: int) -> dict[str, str]:
    """Fetch all verses of a chapter in one range request."""
    url = f"{SEFARIA_API}/{ref}.{chapter}.1-{verse_count}?language=he&context=0"
    try:
        data = get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise
    he = data.get("he", [])
    result: dict[str, str] = {}
    for i, verse_segments in enumerate(he):
        text = flatten(verse_segments)
        if text:
            result[str(i + 1)] = text
    return result


def fetch_book(abbrev: str, ref: str) -> dict[str, dict[str, str]]:
    chapters_shape = fetch_shape(ref)
    if not chapters_shape:
        print(f"    No shape data for {ref}, skipping")
        return {}

    result: dict[str, dict[str, str]] = {}
    for ch_idx, verse_counts in enumerate(chapters_shape):
        ch = ch_idx + 1
        if not isinstance(verse_counts, list) or len(verse_counts) == 0:
            continue
        verse_count = len(verse_counts)
        ch_data = fetch_chapter(ref, ch, verse_count)
        if ch_data:
            result[str(ch)] = ch_data
        time.sleep(0.4)

    return result


def main() -> None:
    import sys

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = sys.argv[1:] if len(sys.argv) > 1 else list(BOOKS.keys())
    unknown = [t for t in targets if t not in BOOKS]
    if unknown:
        print(f"Unknown books: {unknown}. Valid: {list(BOOKS)}")
        sys.exit(1)

    for abbrev in targets:
        ref = BOOKS[abbrev]
        out_path = OUTPUT_DIR / f"{abbrev.lower()}.json"
        print(f"  {abbrev}: fetching from Sefaria…")
        data = fetch_book(abbrev, ref)
        verse_count = sum(len(v) for v in data.values())
        out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        print(f"    → {len(data)} chapters, {verse_count} verses")

    print("Done.")


if __name__ == "__main__":
    main()
