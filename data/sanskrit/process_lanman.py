#!/usr/bin/env python3
"""
OCR Lanman's Sanskrit Reader (1963 ed.) and produce static JSON.

Requirements:
  brew install poppler tesseract tesseract-lang
  pip install indic-transliteration

Usage:
  python data/sanskrit/process_lanman.py
  python data/sanskrit/process_lanman.py I III  # specific selections

Output: frontend/public/data/sanskrit/lanman.json
Format:
  {
    "selections": [
      {
        "num": 1,
        "numeral": "I",
        "title": "Nala",
        "source": "Mahā-bhārata",
        "pages": [1, 2, ...],
        "devanagari": "...",
        "iast": "..."
      },
      ...
    ]
  }

Page offset: PDF page = book page + 17
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Table of Contents — (numeral, title, source, book_start, book_end)
# book_end is inclusive; last selection in a range gets end from next entry - 1
# ---------------------------------------------------------------------------
TOC = [
    ("I",      "Nala",                    "Mahā-bhārata",           1,   8),
    ("II",     "The Brahman and the Pots","Hitopadeça",              9,  10),
    ("III",    "The Ungrateful Man",       "Hitopadeça",             11,  12),
    ("IV",     "The Lion and the Hare",    "Hitopadeça",             13,  15),
    ("V",      "The Crow and the Snake",   "Hitopadeça",             16,  17),
    ("VI",     "The Frogs and the Snake",  "Hitopadeça",             18,  19),
    ("VII",    "The Ass in the Tiger-skin","Hitopadeça",             20,  20),
    ("VIII",   "The Weaver as Viṣṇu",     "Hitopadeça",             21,  22),
    ("IX",     "The Scheming Wife",        "Hitopadeça",             23,  24),
    ("X",      "The Brahman's Wife and the Mongoose", "Hitopadeça", 25,  26),
    ("XI",     "Supersession of Older Brothers","Hitopadeça",        27,  27),
    ("XII",    "Sañjīvaka and Piṅgalaka",  "Hitopadeça",            28,  29),
    ("XIII",   "The Brahman's Dream",      "Hitopadeça",             30,  31),
    ("XIV",    "The Turtle who talked too much","Hitopadeça",        32,  33),
    ("XV",     "The Merchant's Son",       "Hitopadeça",             34,  35),
    ("XVI",    "The Ascetic and the Mouse","Hitopadeça",             36,  37),
    ("XVII",   "The Poisoned Food",        "Hitopadeça",             38,  38),
    ("XVIII",  "The Barber who killed the Monks","Hitopadeça",       39,  40),
    ("XIX",    "The Credulous Husband",    "Hitopadeça",             41,  42),
    ("XX",     "The Weaver, the Princess, and the Prince","Hitopadeça",43,44),
    ("XXI",    "Conclusion of Book IV",    "Hitopadeça",             44,  44),
    ("XXII",   "The Brahman Haridatta",    "Kathā-sarit-sāgara",    45,  46),
    ("XXIII",  "The Two Friends",          "Kathā-sarit-sāgara",    47,  47),
    ("XXIV",   "The King and the Monk",    "Kathā-sarit-sāgara",    48,  48),
    ("XXV",    "The Stolen Necklace",      "Kathā-sarit-sāgara",    49,  50),
    ("XXVI",   "The Brahman and the Barber","Kathā-sarit-sāgara",   51,  51),
    ("XXVII",  "The Foolish Sons",         "Kathā-sarit-sāgara",    52,  55),
    ("XXVIII", "Laws of Manu",             "Manu-smṛti",            56,  65),
    ("XXIX",   "Riddle of the Waters",     "Ṛgveda",                66,  67),
    ("XXX",    "Riddle of the Year",       "Ṛgveda",                68,  68),
    ("XXXI",   "Hymn to Indra I",          "Ṛgveda",                69,  69),
    ("XXXII",  "Hymn to Indra II",         "Ṛgveda",                70,  70),
    ("XXXIII", "Hymn to Indra III",        "Ṛgveda",                71,  71),
    ("XXXIV",  "Hymn to Indra IV",         "Ṛgveda",                72,  72),
    ("XXXV",   "Hymn to Agni I",           "Ṛgveda",                73,  73),
    ("XXXVI",  "Hymn to Agni II",          "Ṛgveda",                74,  74),
    ("XXXVII", "Hymn to Agni III",         "Ṛgveda",                75,  75),
    ("XXXVIII","Hymn to Agni IV",          "Ṛgveda",                76,  76),
    ("XXXIX",  "Hymn to Soma",             "Ṛgveda",                77,  77),
    ("XL",     "Hymn to the Maruts",       "Ṛgveda",                78,  78),
    ("XLI",    "Hymn to Varuṇa I",        "Ṛgveda",                79,  79),
    ("XLII",   "Hymn to Varuṇa II",       "Ṛgveda",                80,  80),
    ("XLIII",  "Hymn to Varuṇa III",      "Ṛgveda",                81,  81),
    ("XLIV",   "Hymn to Varuṇa IV",       "Ṛgveda",                82,  82),
    ("XLV",    "Hymn to Varuṇa V",        "Ṛgveda",                83,  83),
    ("XLVI",   "Hymn to Viṣṇu",          "Ṛgveda",                 84,  84),
    ("XLVII",  "Dawn Hymn I",              "Ṛgveda",                85,  85),
    ("XLVIII", "Dawn Hymn II",             "Ṛgveda",                86,  86),
    ("XLIX",   "Dawn Hymn III",            "Ṛgveda",                87,  87),
    ("L",      "Creation Hymn",            "Ṛgveda",                88,  88),
    ("LI",     "Purūravas and Urvaçī",    "Ṛgveda",                 89,  89),
    ("LII",    "The Two Birds",            "Ṛgveda",                90,  90),
    ("LIII",   "Dialogue of Yama and Yamī","Ṛgveda",                91,  91),
    ("LIV",    "The One Thing Needful",    "Ṛgveda",                92,  92),  # adjusted
    ("LV",     "Hymn of Man",              "Ṛgveda",                92,  92),  # same page range area
    ("LVI",    "Burial Hymn I",            "Ṛgveda",                93,  93),
    ("LVII",   "Burial Hymn II",           "Ṛgveda",                94,  94),
    ("LVIII",  "Wedding Hymn I",           "Ṛgveda",                95,  95),
    ("LIX",    "Wedding Hymn II",          "Ṛgveda",                96,  96),
    ("LX",     "Hymn to Night",            "Ṛgveda",                97,  97),
    ("LXI",    "Hymn to the Frog",         "Ṛgveda",                98,  98),  # adjusted
    ("LXII",   "Maitrāyaṇī I",           "Maitrāyaṇī-saṃhitā",    91,  91),  # pages from summary
    ("LXIII",  "Maitrāyaṇī II",          "Maitrāyaṇī-saṃhitā",    92,  92),
    ("LXIV",   "Maitrāyaṇī III",         "Maitrāyaṇī-saṃhitā",    93,  93),
    ("LXV",    "Maitrāyaṇī IV",          "Maitrāyaṇī-saṃhitā",    93,  93),
    ("LXVI",   "Brāhmaṇa I",             "Aitareya-brāhmaṇa",     93,  94),
    ("LXVII",  "Brāhmaṇa II",            "Aitareya-brāhmaṇa",     94,  94),
    ("LXVIII", "Brāhmaṇa III",           "Çatapatha-brāhmaṇa",    95,  95),
    ("LXIX",   "Brāhmaṇa IV",            "Çatapatha-brāhmaṇa",    95,  96),
    ("LXX",    "Brāhmaṇa V",             "Çatapatha-brāhmaṇa",    96,  96),
    ("LXXI",   "Brāhmaṇa VI",            "Taittirīya-brāhmaṇa",   97,  97),
    ("LXXII",  "Brāhmaṇa VII",           "Taittirīya-brāhmaṇa",   97,  97),
    ("LXXIII", "Brāhmaṇa VIII",          "Taittirīya-brāhmaṇa",   98,  98),  # adjusted
    ("LXXIV",  "Gṛhya-sūtra I",          "Āçvalāyana-gṛhya-sūtra",98, 100),
    ("LXXV",   "Gṛhya-sūtra II",         "Pāraskara-gṛhya-sūtra", 101, 101),
]

PAGE_OFFSET = 17  # PDF_page = book_page + PAGE_OFFSET

PDF_PATH = Path(__file__).parents[2] / "pdf" / "Lanman's_Sanskrit_Reader.pdf"
OUTPUT_PATH = Path(__file__).parents[2] / "frontend" / "public" / "data" / "sanskrit" / "lanman.json"


def pdf_page(book_page: int) -> int:
    return book_page + PAGE_OFFSET


def ocr_page(pdf_path: Path, page_num: int, tmpdir: str) -> str:
    """Render a single PDF page and OCR it with Tesseract Sanskrit."""
    base = os.path.join(tmpdir, f"page_{page_num:04d}")
    png = base + ".png"

    # pdftoppm: -f/-l are 1-based page numbers
    subprocess.run(
        ["pdftoppm", "-r", "300", "-f", str(page_num), "-l", str(page_num),
         "-png", "-singlefile", str(pdf_path), base],
        check=True, capture_output=True,
    )

    if not os.path.exists(png):
        # pdftoppm may append -NNNN.png
        candidates = [f for f in os.listdir(tmpdir) if f.startswith(f"page_{page_num:04d}") and f.endswith(".png")]
        if candidates:
            png = os.path.join(tmpdir, candidates[0])
        else:
            return ""

    result = subprocess.run(
        ["tesseract", png, "stdout", "-l", "san", "--psm", "6"],
        capture_output=True, text=True,
    )
    return result.stdout


def clean_ocr(text: str) -> str:
    """Remove Tesseract artifacts and page noise."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip likely page numbers (short numeric-ish lines)
        if re.fullmatch(r"[\d\s\-–—.]+", stripped):
            continue
        # Skip very short lines that are probably headers/footers
        if len(stripped) <= 3:
            continue
        cleaned.append(line.rstrip())

    # Collapse runs of blank lines to single blank
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned))
    return result.strip()


def devanagari_to_iast(text: str) -> str:
    """Convert Devanagari to IAST via indic_transliteration."""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(text, sanscript.DEVANAGARI, sanscript.IAST)
    except ImportError:
        return ""


def process_selection(entry: tuple, tmpdir: str) -> dict:
    numeral, title, source, book_start, book_end = entry
    num = roman_to_int(numeral)

    pages = list(range(pdf_page(book_start), pdf_page(book_end) + 1))
    print(f"  {numeral}: {title} ({source}) — PDF pages {pages[0]}–{pages[-1]}")

    devanagari_parts = []
    for p in pages:
        raw = ocr_page(PDF_PATH, p, tmpdir)
        devanagari_parts.append(clean_ocr(raw))

    devanagari = "\n\n".join(p for p in devanagari_parts if p)
    iast = devanagari_to_iast(devanagari)

    return {
        "num": num,
        "numeral": numeral,
        "title": title,
        "source": source,
        "bookPages": [book_start, book_end],
        "devanagari": devanagari,
        "iast": iast,
    }


ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(s: str) -> int:
    s = s.split()[0]  # handle "XXVIII" etc.
    result = 0
    prev = 0
    for ch in reversed(s):
        val = ROMAN.get(ch, 0)
        if val < prev:
            result -= val
        else:
            result += val
        prev = val
    return result


def main() -> None:
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}")
        sys.exit(1)

    for tool in ("pdftoppm", "tesseract"):
        if not shutil.which(tool):
            print(f"Missing tool: {tool}. Install with: brew install {'poppler' if tool == 'pdftoppm' else 'tesseract tesseract-lang'}")
            sys.exit(1)

    targets_arg = sys.argv[1:]
    numeral_set = {e[0] for e in TOC}
    if targets_arg:
        unknown = [t for t in targets_arg if t not in numeral_set]
        if unknown:
            print(f"Unknown selections: {unknown}")
            sys.exit(1)
        entries = [e for e in TOC if e[0] in targets_arg]
    else:
        entries = TOC

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data if doing a partial run
    existing: dict[str, dict] = {}
    if OUTPUT_PATH.exists() and targets_arg:
        data = json.loads(OUTPUT_PATH.read_text())
        existing = {s["numeral"]: s for s in data.get("selections", [])}

    selections = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for entry in entries:
            sel = process_selection(entry, tmpdir)
            existing[sel["numeral"]] = sel

    # Reconstruct ordered list
    numeral_order = [e[0] for e in TOC]
    for numeral in numeral_order:
        if numeral in existing:
            selections.append(existing[numeral])

    output = {"selections": selections}
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nWrote {len(selections)} selections → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
