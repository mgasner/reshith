"""Fetch STEPBible TALXX (Septuagint) and Brenton English translation data.

Data sources (CC BY 4.0 / public domain):
  TALXX   — https://github.com/tyndale/STEPBible-Data
  Brenton — https://github.com/eliranwong/LXX-Rahlfs-1935 or similar

Outputs:
  data/nt_greek/TALXX.txt        — STEPBible Translators Amalgamated LXX
  data/nt_greek/brenton_lxx.json — Brenton translation (book→chapter→verse→text)

Usage:
  cd data/nt_greek
  python prepare_lxx.py
"""

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

TALXX_URL = (
    "https://raw.githubusercontent.com/tyndale/STEPBible-Data/master/"
    "Translators%20Amalgamated%20LXX%20-%20STEPBible.org%20CC%20BY.txt"
)

# Brenton LXX English translation — scrollmapper eng-lxx (public domain)
BRENTON_URL = (
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/"
    "json/t_lxx.json"
)

# Map scrollmapper book IDs to LXX abbreviations
_SCROLL_ID_TO_ABBREV = {
    1: "Gen", 2: "Exo", 3: "Lev", 4: "Num", 5: "Deu",
    6: "Jos", 7: "Jdg", 8: "Rut", 9: "1Sa", 10: "2Sa",
    11: "1Ki", 12: "2Ki", 13: "1Ch", 14: "2Ch",
    15: "Ezr", 16: "Neh", 17: "Est",
    18: "Job", 19: "Psa", 20: "Pro", 21: "Ecc", 22: "Sng",
    23: "Isa", 24: "Jer", 25: "Lam", 26: "Ezk", 27: "Dan",
    28: "Hos", 29: "Jol", 30: "Amo", 31: "Oba", 32: "Jon",
    33: "Mic", 34: "Nah", 35: "Hab", 36: "Zep", 37: "Hag",
    38: "Zec", 39: "Mal",
    # Deuterocanon (IDs vary by source — adjust if needed)
    68: "Tob", 69: "Jdt", 70: "1Ma", 71: "2Ma",
    73: "Wis", 74: "Sir", 75: "Bar",
}


def fetch(url: str, label: str) -> bytes:
    print(f"Fetching {label}…", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "reshith/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"  {len(data):,} bytes", flush=True)
    return data


def fetch_talxx() -> None:
    out = HERE / "TALXX.txt"
    if out.exists():
        print(f"TALXX.txt already exists ({out.stat().st_size:,} bytes), skipping.")
        return
    data = fetch(TALXX_URL, "TALXX")
    out.write_bytes(data)
    print(f"Wrote {out}")


def fetch_brenton() -> None:
    out = HERE / "brenton_lxx.json"
    if out.exists():
        print(f"brenton_lxx.json already exists, skipping.")
        return
    try:
        data = fetch(BRENTON_URL, "Brenton LXX")
        raw = json.loads(data.decode("utf-8"))

        result: dict[str, dict[str, dict[str, str]]] = {}
        rows = raw.get("resultset", {}).get("row", [])
        for row in rows:
            fields = row.get("field", [])
            if len(fields) < 4:
                continue
            book_id = int(fields[0])
            ch = str(int(fields[1]))
            v = str(int(fields[2]))
            text = str(fields[3])
            abbrev = _SCROLL_ID_TO_ABBREV.get(book_id)
            if abbrev is None:
                continue
            result.setdefault(abbrev, {}).setdefault(ch, {})[v] = text

        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out} ({len(result)} books)")
    except Exception as e:
        print(f"  Warning: could not fetch Brenton translation: {e}")
        print("  You can manually supply data/nt_greek/brenton_lxx.json")
        print("  Format: {abbrev: {chapter_str: {verse_str: text}}}")


if __name__ == "__main__":
    try:
        fetch_talxx()
        fetch_brenton()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
