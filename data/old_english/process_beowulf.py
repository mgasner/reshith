#!/usr/bin/env python3
"""
Process a raw Old English text file of Beowulf into structured JSON.

Scholarly standard: Klaeber's Beowulf, 4th edition (Klaeber 4), edited by
R. D. Fulk, Robert E. Bjork, and John D. Niles (University of Toronto Press,
2008). The text uses the standard normalized scholarly orthography of that
edition, which preserves the distinction between þ (thorn) and ð (eth) and
marks long vowels with macrons (ā, ē, ī, ō, ū).

Input format:
  A plain-text file with one half-line pair per line, tab-delimited:
    <line_num>\t<a-verse>\t<b-verse>

  Section boundaries are marked with a comment line beginning with #:
    # FITT I: The Spear-Danes (lines 1-52)

Usage:
  python data/old_english/process_beowulf.py [input.txt]

  Defaults to reading from data/old_english/beowulf_raw.txt if no argument given.

Output:
  frontend/public/data/old_english/beowulf.json

Output format:
  {
    "title": "Beowulf",
    "date": "c. 700-1000 CE",
    "manuscript": "British Library, Cotton Vitellius A.xv",
    "sections": [
      {
        "id": "fitt-1",
        "num": "I",
        "title": "The Spear-Danes",
        "lineStart": 1,
        "lineEnd": 52,
        "lines": [
          {
            "num": 1,
            "a": "Hwæt! We Gardena",
            "b": "in geardagum,",
            "translation": "..."
          },
          ...
        ]
      }
    ]
  }

Notes:
- Old English special characters used in this edition:
    þ (thorn) = /θ/ as in 'thin'
    ð (eth)   = /ð/ as in 'this' (originally interchangeable with þ in OE MSS)
    æ (ash)   = /æ/ as in 'cat'
    ƿ (wynn)  = /w/ (rarely used in normalized editions; usually written as w)
    ā ē ī ō ū = long vowels

- The alliterative verse structure: each line consists of two half-lines
  (hemistichs) separated by a caesura. The a-verse and b-verse alliterate
  on the first stressed syllable of the b-verse, which matches one or both
  stressed syllables of the a-verse.

- Translations are not included in the raw text file and must be supplied
  separately (e.g., from a scholarly parallel-text edition such as
  Chickering's Beowulf, 2006, or Mitchell & Robinson's Beowulf, 1998).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Table of fitts (sections)
# ---------------------------------------------------------------------------

FITTS = [
    {
        "id": "fitt-1",
        "num": "I",
        "title": "The Spear-Danes",
        "lineStart": 1,
        "lineEnd": 52,
    },
    {
        "id": "fitt-2",
        "num": "II",
        "title": "Heorot",
        "lineStart": 53,
        "lineEnd": 114,
    },
    {
        "id": "fitt-3",
        "num": "III",
        "title": "Grendel's Ravages",
        "lineStart": 115,
        "lineEnd": 193,
    },
    {
        "id": "fitt-4",
        "num": "IV",
        "title": "Beowulf's Voyage",
        "lineStart": 194,
        "lineEnd": 257,
    },
    {
        "id": "fitt-5",
        "num": "V",
        "title": "Arrival at Heorot",
        "lineStart": 258,
        "lineEnd": 319,
    },
    # Additional fitts (VI–XLIII) not yet encoded
]

INPUT_PATH = Path(__file__).parents[2] / "data" / "old_english" / "beowulf_raw.txt"
OUTPUT_PATH = (
    Path(__file__).parents[2]
    / "frontend"
    / "public"
    / "data"
    / "old_english"
    / "beowulf.json"
)


def parse_raw(text: str) -> dict[int, tuple[str, str]]:
    """Parse tab-delimited raw text into {line_num: (a_verse, b_verse)}."""
    lines: dict[int, tuple[str, str]] = {}
    for raw_line in text.splitlines():
        raw_line = raw_line.strip()
        if not raw_line or raw_line.startswith("#"):
            continue
        parts = raw_line.split("\t")
        if len(parts) < 3:
            continue
        try:
            num = int(parts[0])
        except ValueError:
            continue
        a_verse = parts[1].strip()
        b_verse = parts[2].strip()
        lines[num] = (a_verse, b_verse)
    return lines


def assign_to_fitts(
    verse_map: dict[int, tuple[str, str]],
    translations: dict[int, str] | None = None,
) -> list[dict]:
    """Group parsed verses into fitt sections."""
    sections = []
    for fitt in FITTS:
        fitt_lines = []
        for num in range(fitt["lineStart"], fitt["lineEnd"] + 1):
            if num not in verse_map:
                continue
            a, b = verse_map[num]
            entry: dict = {"num": num, "a": a, "b": b}
            if translations and num in translations:
                entry["translation"] = translations[num]
            fitt_lines.append(entry)

        section = dict(fitt)
        section["lines"] = fitt_lines
        sections.append(section)
    return sections


def build_output(sections: list[dict]) -> dict:
    return {
        "title": "Beowulf",
        "date": "c. 700\u20131000 CE",
        "manuscript": "British Library, Cotton Vitellius A.xv",
        "sections": sections,
    }


def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_PATH

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        print("Provide a tab-delimited raw text file as the first argument.")
        sys.exit(1)

    raw_text = input_path.read_text(encoding="utf-8")
    verse_map = parse_raw(raw_text)

    print(f"Parsed {len(verse_map)} verse-lines from {input_path}")

    sections = assign_to_fitts(verse_map)

    output = build_output(sections)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    total_lines = sum(len(s["lines"]) for s in sections)
    print(f"Wrote {total_lines} lines across {len(sections)} fitts → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
