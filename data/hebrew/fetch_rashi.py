#!/usr/bin/env python3
"""
Download Rashi commentary from Sefaria API and save as static JSON.

Output: frontend/public/data/hebrew/rashi/{abbrev}.json
Format: { "chapter": { "verse": "html text", ... }, ... }  (1-based string keys)

Run from repo root:
  python data/hebrew/fetch_rashi.py          # all books
  python data/hebrew/fetch_rashi.py Gen Exo  # specific books

Strategy:
  1. Fetch the book's shape from Sefaria to get verse counts per chapter.
  2. For each chapter, fetch the full range {ref}.{ch}.1-{n} in one request.
     The response `he` is a list-of-lists: he[verse_idx] = [segment, ...].
  3. Join segments and skip empty verses.

Rashi has depth-3 references (Chapter.Verse.Comment), so requesting
{ref}.{ch} alone returns only verse 1's comments. The range syntax fixes this.
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

SEFARIA_API = "https://www.sefaria.org/api/texts"
SEFARIA_SHAPE = "https://www.sefaria.org/api/shape"

# TAHOT abbrev → Sefaria ref (underscored)
# Chronicles intentionally absent — Rashi did not comment on them.
BOOKS: dict[str, str] = {
    "Gen": "Rashi_on_Genesis",
    "Exo": "Rashi_on_Exodus",
    "Lev": "Rashi_on_Leviticus",
    "Num": "Rashi_on_Numbers",
    "Deu": "Rashi_on_Deuteronomy",
    "Jos": "Rashi_on_Joshua",
    "Jdg": "Rashi_on_Judges",
    "1Sa": "Rashi_on_I_Samuel",
    "2Sa": "Rashi_on_II_Samuel",
    "1Ki": "Rashi_on_I_Kings",
    "2Ki": "Rashi_on_II_Kings",
    "Ezr": "Rashi_on_Ezra",
    "Neh": "Rashi_on_Nehemiah",
    "Est": "Rashi_on_Esther",
    "Job": "Rashi_on_Job",
    "Psa": "Rashi_on_Psalms",
    "Pro": "Rashi_on_Proverbs",
    "Ecc": "Rashi_on_Ecclesiastes",
    "Sng": "Rashi_on_Song_of_Songs",
    "Isa": "Rashi_on_Isaiah",
    "Jer": "Rashi_on_Jeremiah",
    "Lam": "Rashi_on_Lamentations",
    "Ezk": "Rashi_on_Ezekiel",
    "Dan": "Rashi_on_Daniel",
    "Hos": "Rashi_on_Hosea",
    "Jol": "Rashi_on_Joel",
    "Amo": "Rashi_on_Amos",
    "Oba": "Rashi_on_Obadiah",
    "Jon": "Rashi_on_Jonah",
    "Mic": "Rashi_on_Micah",
    "Nah": "Rashi_on_Nahum",
    "Hab": "Rashi_on_Habakkuk",
    "Zep": "Rashi_on_Zephaniah",
    "Hag": "Rashi_on_Haggai",
    "Zec": "Rashi_on_Zechariah",
    "Mal": "Rashi_on_Malachi",
}

OUTPUT_DIR = Path(__file__).parents[2] / "frontend" / "public" / "data" / "hebrew" / "rashi"


def get(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "reshith-rashi-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def flatten(text: object) -> str:
    """Flatten a possibly-nested Sefaria segment list to a single HTML string."""
    if isinstance(text, str):
        return text.strip()
    if isinstance(text, list):
        return " ".join(flatten(t) for t in text if t).strip()
    return ""


def fetch_shape(ref: str) -> list[list[int]]:
    """Return chapters[ch_idx] = [comment_count_per_verse, ...]."""
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
