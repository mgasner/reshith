"""TBESH / TBESG — STEPBible Extended Strongs lexicons (CC BY 4.0).

Parses the two TSV files on first access and builds in-memory indices keyed by
dStrong ID (e.g. H0776G, G0025).  Lookup falls back gracefully:

  1. Exact dStrong match (e.g. H0776G)
  2. eStrong# match (e.g. H0776)
  3. After stripping instance-disambiguation suffix _A/_B (H5921A_A → H5921A)
"""

import re
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parents[3] / "data"
TBESH_FILE = DATA_DIR / "hebrew" / "TBESH.txt"
TBESG_FILE = DATA_DIR / "greek" / "TBESG.txt"


@dataclass
class StrongsEntry:
    strongs_id: str       # dStrong ID, e.g. H0001G, G0025
    e_strongs_id: str     # eStrong# ID, e.g. H0001, G0025
    native: str           # Hebrew / Greek form
    transliteration: str
    morph: str            # e.g. H:N-M
    gloss: str            # short one-word definition
    meaning: str          # longer HTML definition


# dStrong → entry (each dStrong sub-entry has its own row)
_HEB_BY_DSTRONG: dict[str, StrongsEntry] = {}
_GRK_BY_DSTRONG: dict[str, StrongsEntry] = {}
# eStrong# → first entry found (fallback)
_HEB_BY_ESTRONG: dict[str, StrongsEntry] = {}
_GRK_BY_ESTRONG: dict[str, StrongsEntry] = {}

_loaded = False

# Matches the Strong's number at the start of the dStrong column, e.g. "H0001G ="
_DSTRONG_RE = re.compile(r'^([HGANhgan]\d+[A-Za-z]*)')
# Valid eStrong# format: H/G/A/N followed by digits and optional letters
_ESTRONG_RE = re.compile(r'^[HGANhgan]\d+[A-Za-z]*$')
# Instance-disambiguation suffix like _A, _B
_DISAMBIG_RE = re.compile(r'_[A-Z]$')
# Letter suffix for fallback: H0001G → H0001
_LETTER_SUFFIX_RE = re.compile(r'^([HGA]\d+)[A-Z]$')


def _parse_file(filepath: Path, is_hebrew: bool) -> None:
    if not filepath.exists():
        return

    by_dstrong = _HEB_BY_DSTRONG if is_hebrew else _GRK_BY_DSTRONG
    by_estrong = _HEB_BY_ESTRONG if is_hebrew else _GRK_BY_ESTRONG

    past_header = False
    with open(filepath, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not past_header:
                if line.startswith("eStrong#\t"):
                    past_header = True
                continue

            # Skip blank lines, section markers, sub-entries
            if not line or line.startswith(("$", "-", "\t", "#")):
                continue

            parts = line.split("\t")
            if len(parts) < 7:
                continue

            e_strong = parts[0].strip()
            # Only accept canonical Strong's numbers (H/G/A/N + digits)
            if not _ESTRONG_RE.match(e_strong):
                continue

            # Parse dStrong from column 1 (e.g. "H0001G =" → "H0001G")
            m = _DSTRONG_RE.match(parts[1].strip())
            d_strong = m.group(1) if m else e_strong

            entry = StrongsEntry(
                strongs_id=d_strong,
                e_strongs_id=e_strong,
                native=parts[3].strip() if len(parts) > 3 else "",
                transliteration=parts[4].strip() if len(parts) > 4 else "",
                morph=parts[5].strip() if len(parts) > 5 else "",
                gloss=parts[6].strip() if len(parts) > 6 else "",
                meaning=parts[7].strip() if len(parts) > 7 else "",
            )

            by_dstrong[d_strong] = entry
            # Keep first entry for each eStrong# as the fallback
            if e_strong not in by_estrong:
                by_estrong[e_strong] = entry


def _ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _parse_file(TBESH_FILE, is_hebrew=True)
    _parse_file(TBESG_FILE, is_hebrew=False)
    _loaded = True


def get_entry(strongs_id: str) -> StrongsEntry | None:
    """Look up a TBESH/TBESG entry by dStrong or eStrong ID.

    Handles:
    - dStrong IDs like H0776G, H0430G, G0025
    - eStrong IDs like H0776, G0025
    - Instance-disambiguation suffixes like H5921A_A → H5921A
    """
    _ensure_loaded()
    if not strongs_id:
        return None

    # Strip instance-disambiguation suffix (_A, _B …)
    clean = _DISAMBIG_RE.sub("", strongs_id)

    is_hebrew = clean[0].upper() in ("H", "A", "N") if clean else True
    by_dstrong = _HEB_BY_DSTRONG if is_hebrew else _GRK_BY_DSTRONG
    by_estrong = _HEB_BY_ESTRONG if is_hebrew else _GRK_BY_ESTRONG

    # 1. Exact dStrong match
    if clean in by_dstrong:
        return by_dstrong[clean]

    # 2. Try as eStrong# (for IDs without letter suffix like H1961)
    if clean in by_estrong:
        return by_estrong[clean]

    # 3. Try stripping a single letter suffix: H0001G → H0001
    m = _LETTER_SUFFIX_RE.match(clean)
    if m:
        base = m.group(1)
        if base in by_estrong:
            return by_estrong[base]

    return None
