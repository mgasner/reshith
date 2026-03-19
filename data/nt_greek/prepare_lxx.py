"""Fetch LXX morphological data from nathans/lxxmorph-unicode.

Data source:
  CCAT Morphological Septuagint (Unicode edition by Nathan Smith)
  https://github.com/nathans/lxxmorph-unicode
  Based on CCAT/Packard Humanities Institute data (freely available for scholarly use)

Output:
  data/nt_greek/TALXX.txt  — tab-separated interlinear LXX data, format:
      Book.ch.v#tok=T  greek  (empty)  (empty)  (empty)  catss_grammar  (empty)  (empty)  lemma

Note: Brenton English translation is not bundled here. The brenton_lxx.json
      file can be supplied separately; the viewer gracefully shows Greek-only
      if it is absent.

Usage:
  cd data/nt_greek
  python3 prepare_lxx.py
"""

import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW_BASE = "https://raw.githubusercontent.com/nathans/lxxmorph-unicode/master"

# (filename, our book abbreviation)
# Using B-text for Joshua and Judges; DanielTh (Theodotion) for Daniel.
# 2Esdras covers Ezra + Nehemiah in LXX numbering — stored as "Ezr" here.
BOOK_FILES: list[tuple[str, str]] = [
    ("01.Gen.txt", "Gen"),
    ("02.Exod.txt", "Exo"),
    ("03.Lev.txt", "Lev"),
    ("04.Num.txt", "Num"),
    ("05.Deut.txt", "Deu"),
    ("06.JoshB.txt", "Jos"),
    ("08.JudgesB.txt", "Jdg"),
    ("10.Ruth.txt", "Rut"),
    ("11.1Sam.txt", "1Sa"),
    ("12.2Sam.txt", "2Sa"),
    ("13.1Kings.txt", "1Ki"),
    ("14.2Kings.txt", "2Ki"),
    ("15.1Chron.txt", "1Ch"),
    ("16.2Chron.txt", "2Ch"),
    ("18.2Esdras.txt", "Ezr"),
    ("19.Esther.txt", "Est"),
    ("20.Judith.txt", "Jdt"),
    ("21.TobitBA.txt", "Tob"),
    ("23.1Macc.txt", "1Ma"),
    ("24.2Macc.txt", "2Ma"),
    ("25.3Macc.txt", "3Ma"),
    ("26.4Macc.txt", "4Ma"),
    ("27.Psalms.txt", "Psa"),
    ("29.Proverbs.txt", "Pro"),
    ("30.Qoheleth.txt", "Ecc"),
    ("31.Canticles.txt", "Sng"),
    ("32.Job.txt", "Job"),
    ("33.Wisdom.txt", "Wis"),
    ("34.Sirach.txt", "Sir"),
    ("36.Hosea.txt", "Hos"),
    ("37.Micah.txt", "Mic"),
    ("38.Amos.txt", "Amo"),
    ("39.Joel.txt", "Jol"),
    ("40.Jonah.txt", "Jon"),
    ("41.Obadiah.txt", "Oba"),
    ("42.Nahum.txt", "Nah"),
    ("43.Habakkuk.txt", "Hab"),
    ("44.Zeph.txt", "Zep"),
    ("45.Haggai.txt", "Hag"),
    ("46.Zech.txt", "Zec"),
    ("47.Malachi.txt", "Mal"),
    ("48.Isaiah.txt", "Isa"),
    ("49.Jer.txt", "Jer"),
    ("50.Baruch.txt", "Bar"),
    ("52.Lam.txt", "Lam"),
    ("53.Ezek.txt", "Ezk"),
    ("57.DanielTh.txt", "Dan"),
]

# Verse header formats:
#   "Gen 1:1"     → chapter=1, verse=1   (standard)
#   "Obad 1"      → chapter=1, verse=1   (single-chapter books: no colon, verse only)
VERSE_HEADER_RE = re.compile(r"^\S+\s+(\d+):(\d+)")
VERSE_HEADER_SINGLE_RE = re.compile(r"^\S+\s+(\d+)$")


def fetch(url: str, label: str) -> str:
    print(f"  Fetching {label}…", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "reshith/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    print(f"    {len(data):,} bytes", flush=True)
    return data.decode("utf-8", errors="replace")


def convert_book(text: str, abbrev: str) -> list[str]:
    """Convert one lxxmorph file into TALXX.txt lines."""
    lines: list[str] = []
    chapter = 0
    verse = 0
    token = 0

    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue

        m = VERSE_HEADER_RE.match(raw)
        if m:
            chapter = int(m.group(1))
            verse = int(m.group(2))
            token = 0
            continue

        # Single-chapter books: "Obad 1" means chapter=1, verse=1
        m2 = VERSE_HEADER_SINGLE_RE.match(raw)
        if m2 and raw[0].isupper():
            chapter = 1
            verse = int(m2.group(1))
            token = 0
            continue

        if chapter == 0:
            continue  # skip pre-data header lines

        parts = raw.split()
        if len(parts) < 2:
            continue

        greek = parts[0]
        grammar = parts[1]
        lemma = parts[2] if len(parts) > 2 else ""

        token += 1
        ref = f"{abbrev}.{chapter}.{verse}#{token:02d}=T"
        # Tab-separated: ref, greek, "", "", "", grammar, "", "", lemma
        lines.append(f"{ref}\t{greek}\t\t\t\t{grammar}\t\t\t{lemma}")

    return lines


def fetch_talxx() -> None:
    out = HERE / "TALXX.txt"
    if out.exists():
        print(f"TALXX.txt already exists ({out.stat().st_size:,} bytes), skipping.")
        return

    all_lines: list[str] = []
    for filename, abbrev in BOOK_FILES:
        url = f"{RAW_BASE}/{filename}"
        try:
            text = fetch(url, f"{abbrev} ({filename})")
            book_lines = convert_book(text, abbrev)
            all_lines.extend(book_lines)
            print(f"    {abbrev}: {len(book_lines)} word tokens")
        except Exception as e:
            print(f"    Warning: could not fetch {filename}: {e}", file=sys.stderr)

    out.write_text("\n".join(all_lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(all_lines):,} total tokens)")


if __name__ == "__main__":
    print("Fetching LXX morphological data…")
    try:
        fetch_talxx()
        print("Done.")
        print()
        print("Note: Brenton English translation (brenton_lxx.json) must be supplied")
        print("      separately. The LXX viewer works without it (Greek-only mode).")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
