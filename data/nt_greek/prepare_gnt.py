"""Fetch STEPBible TANTT (Greek NT) and KJV NT translation data.

Data sources (CC BY 4.0 / public domain):
  TANTT — https://github.com/tyndale/STEPBible-Data
  KJV   — https://github.com/scrollmapper/bible_databases

Outputs:
  data/nt_greek/TANTT.txt     — STEPBible Translators Amalgamated NT
  data/nt_greek/kjv_nt.json   — KJV NT translation (book→chapter→verse→text)

Usage:
  cd data/nt_greek
  python prepare_gnt.py
"""

import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

TANTT_URL = (
    "https://raw.githubusercontent.com/tyndale/STEPBible-Data/master/"
    "Translators%20Amalgamated%20NT%20-%20STEPBible.org%20CC%20BY.txt"
)

KJV_URL = (
    "https://raw.githubusercontent.com/scrollmapper/bible_databases/master/"
    "json/t_kjv.json"
)

# Map scrollmapper book IDs (1–66) to TANTT NT abbreviations
_SCROLL_ID_TO_ABBREV = {
    40: "Mat", 41: "Mrk", 42: "Lke", 43: "Jhn", 44: "Act",
    45: "Rom", 46: "1Co", 47: "2Co", 48: "Gal", 49: "Eph",
    50: "Phl", 51: "Col", 52: "1Th", 53: "2Th", 54: "1Ti",
    55: "2Ti", 56: "Tit", 57: "Phm", 58: "Hbr", 59: "Jas",
    60: "1Pe", 61: "2Pe", 62: "1Jn", 63: "2Jn", 64: "3Jn",
    65: "Jde", 66: "Rev",
}


def fetch(url: str, label: str) -> bytes:
    print(f"Fetching {label}…", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "reshith/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    print(f"  {len(data):,} bytes", flush=True)
    return data


def fetch_tantt() -> None:
    out = HERE / "TANTT.txt"
    if out.exists():
        print(f"TANTT.txt already exists ({out.stat().st_size:,} bytes), skipping.")
        return
    data = fetch(TANTT_URL, "TANTT")
    out.write_bytes(data)
    print(f"Wrote {out}")


def fetch_kjv_nt() -> None:
    out = HERE / "kjv_nt.json"
    if out.exists():
        print(f"kjv_nt.json already exists, skipping.")
        return
    data = fetch(KJV_URL, "KJV")
    raw = json.loads(data.decode("utf-8"))

    # scrollmapper format: {"resultset": {"row": [{"field": [b, c, v, text]}, ...]}}
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
            continue  # skip OT
        result.setdefault(abbrev, {}).setdefault(ch, {})[v] = text

    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(result)} books)")


if __name__ == "__main__":
    try:
        fetch_tantt()
        fetch_kjv_nt()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
