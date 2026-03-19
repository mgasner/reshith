"""Fetch STEPBible TAGNT (Greek NT) and KJV NT translation data.

Data sources (CC BY 4.0 / public domain):
  TAGNT  — https://github.com/STEPBible/STEPBible-Data
           (repo moved from tyndale/ to STEPBible/ org; TANTT split into 2 TAGNT files)
  KJV    — https://github.com/scrollmapper/bible_databases

Outputs:
  data/nt_greek/TAGNT.txt     — STEPBible Translators Amalgamated Greek NT
                                 (Mat-Jhn and Act-Rev concatenated)
  data/nt_greek/kjv_nt.json   — KJV NT translation (book→chapter→verse→text)

Usage:
  cd data/nt_greek
  python3 prepare_gnt.py
"""

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

_RAW = "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT"
TAGNT_MAT_JHN_URL = f"{_RAW}/TAGNT%20Mat-Jhn%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt"
TAGNT_ACT_REV_URL = f"{_RAW}/TAGNT%20Act-Rev%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt"

KJV_URL = (
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/"
    "formats/json/KJV.json"
)

# scrollmapper KJV.json has 66 books in order (0-indexed); NT starts at index 39 (Matthew)
_NT_BOOK_ABBREVS = [
    "Mat", "Mrk", "Luk", "Jhn", "Act",
    "Rom", "1Co", "2Co", "Gal", "Eph", "Php", "Col",
    "1Th", "2Th", "1Ti", "2Ti", "Tit", "Phm",
    "Heb", "Jas", "1Pe", "2Pe", "1Jn", "2Jn", "3Jn", "Jud", "Rev",
]


def fetch(url: str, label: str) -> bytes:
    print(f"Fetching {label}…", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "reshith/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"  {len(data):,} bytes", flush=True)
    return data


def fetch_tagnt() -> None:
    out = HERE / "TAGNT.txt"
    if out.exists():
        print(f"TAGNT.txt already exists ({out.stat().st_size:,} bytes), skipping.")
        return
    part1 = fetch(TAGNT_MAT_JHN_URL, "TAGNT Mat-Jhn")
    part2 = fetch(TAGNT_ACT_REV_URL, "TAGNT Act-Rev")
    # Concatenate; strip BOM from second file if present
    combined = part1
    if part2.startswith(b"\xef\xbb\xbf"):
        part2 = part2[3:]
    combined = combined + b"\n" + part2
    out.write_bytes(combined)
    print(f"Wrote {out} ({len(combined):,} bytes)")


def fetch_kjv_nt() -> None:
    out = HERE / "kjv_nt.json"
    if out.exists():
        print(f"kjv_nt.json already exists, skipping.")
        return
    data = fetch(KJV_URL, "KJV")
    raw = json.loads(data.decode("utf-8"))

    # New scrollmapper format: {"books": [{"name": "...", "chapters": [{"chapter": N, "verses": [{"verse": N, "text": "..."}]}]}]}
    books = raw.get("books", [])
    result: dict[str, dict[str, dict[str, str]]] = {}

    # NT is books[39..65]
    nt_books = books[39:66]
    for abbrev, book in zip(_NT_BOOK_ABBREVS, nt_books):
        chapters: dict[str, dict[str, str]] = {}
        for ch_data in book.get("chapters", []):
            ch = str(ch_data["chapter"])
            verses: dict[str, str] = {}
            for v_data in ch_data.get("verses", []):
                verses[str(v_data["verse"])] = v_data["text"]
            chapters[ch] = verses
        result[abbrev] = chapters

    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(result)} books)")


if __name__ == "__main__":
    try:
        fetch_tagnt()
        fetch_kjv_nt()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
