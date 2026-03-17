#!/usr/bin/env python3
"""
Fetch DCS (Digital Corpus of Sanskrit) CoNLL-U data for Lanman selections.

Source: https://github.com/OliverHellwig/sanskrit  (CC BY 4.0, Oliver Hellwig)

Downloads relevant chapters, parses CoNLL-U with sandhi groups and morphology,
and writes static JSON to frontend/public/data/sanskrit/lanman/.

Output files:
  01.json          — Nala (MBh 3.50–78)
  hitopadesa.json  — Hitopadeśa books 0–4 (covers Lanman II–XXI)
  28.json          — Manu-smṛti chapters 1–12 (covers Lanman XXVIII)
  {N}.json         — Individual Ṛgveda hymns (Lanman XXIX–LXI)

Usage:
  python data/sanskrit/fetch_dcs.py          # all
  python data/sanskrit/fetch_dcs.py 1 28     # specific selection numbers
  python data/sanskrit/fetch_dcs.py hitop    # keyword targets
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

CACHE_DIR = Path(__file__).parent / "dcs_cache"
OUTPUT_DIR = Path(__file__).parents[2] / "frontend" / "public" / "data" / "sanskrit" / "lanman"
GITHUB_RAW = "https://raw.githubusercontent.com/OliverHellwig/sanskrit/master/dcs/data/conllu/files"

# ── DCS text directory names (as on GitHub) ───────────────────────────────────

DCS_DIR = {
    "mbh":   "Mahābhārata",
    "hitop": "Hitopadeśa",
    "manu":  "Manusmṛti",
    "rv":    "Ṛgveda",
}

# ── Ṛgveda: cumulative 0-based file-number offset per maṇḍala ────────────────
# Standard sūkta counts: M1=191, M2=43, M3=62, M4=58, M5=87, M6=75,
#                        M7=104, M8=103, M9=114, M10=191

_RV_COUNTS = [191, 43, 62, 58, 87, 75, 104, 103, 114, 191]
RV_OFFSET: dict[int, int] = {}
_acc = 0
for _m, _c in enumerate(_RV_COUNTS, start=1):
    RV_OFFSET[_m] = _acc
    _acc += _c


def rv_file_num(mandala: int, sukta: int) -> int:
    return RV_OFFSET[mandala] + (sukta - 1)


# ── DCS chapter ID lookup cache ───────────────────────────────────────────────
# Populated lazily when listing a text directory.

_DIR_CACHE: dict[str, dict[tuple[int, int], str]] = {}  # key → {(book, ch): filename}


def _load_dir(dcs_key: str) -> dict[tuple[int, int], str]:
    """Return {(book, chapter): filename} for a DCS text directory.
    Uses GitHub API listing; caches on disk."""
    if dcs_key in _DIR_CACHE:
        return _DIR_CACHE[dcs_key]

    cache_file = CACHE_DIR / f"{dcs_key}_dir.json"
    if cache_file.exists():
        raw = json.loads(cache_file.read_text())
        _DIR_CACHE[dcs_key] = {tuple(k): v for k, v in raw}  # type: ignore[misc]
        return _DIR_CACHE[dcs_key]

    text_name = DCS_DIR[dcs_key]
    encoded = urllib.parse.quote(text_name, safe="")
    # GitHub lists up to 1000 per page; RV needs page 2 for hymns > 1000
    entries: list[str] = []

    # Get the directory SHA first (Contents API is fine for the parent directory)
    parent_url = f"https://api.github.com/repos/OliverHellwig/sanskrit/contents/dcs/data/conllu/files?per_page=300"
    parent_req = urllib.request.Request(parent_url, headers={"User-Agent": "reshith-dcs/1.0"})
    dir_sha = None
    try:
        with urllib.request.urlopen(parent_req, timeout=30) as r:
            items = json.loads(r.read())
            match = next((i for i in items if isinstance(i, dict) and i.get("name") == text_name), None)
            if match:
                dir_sha = match["sha"]
    except Exception as e:
        print(f"    Warning: could not get directory SHA for {text_name}: {e}")

    if dir_sha:
        # Use Git Trees API — handles directories with >1000 files
        tree_url = f"https://api.github.com/repos/OliverHellwig/sanskrit/git/trees/{dir_sha}?recursive=1"
        tree_req = urllib.request.Request(tree_url, headers={"User-Agent": "reshith-dcs/1.0"})
        try:
            with urllib.request.urlopen(tree_req, timeout=30) as r:
                tree = json.loads(r.read())
                entries = [item["path"] for item in tree.get("tree", []) if isinstance(item, dict)]
        except Exception as e:
            print(f"    Warning: Git Trees API failed for {text_name}: {e}")
    else:
        # Fallback: Contents API with pagination
        for page in range(1, 20):
            api_url = (
                f"https://api.github.com/repos/OliverHellwig/sanskrit/"
                f"contents/dcs/data/conllu/files/{encoded}?per_page=1000&page={page}"
            )
            req = urllib.request.Request(api_url, headers={"User-Agent": "reshith-dcs/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    batch = json.loads(r.read())
                    if not batch:
                        break
                    entries.extend(item["name"] for item in batch if isinstance(item, dict))
            except Exception as e:
                print(f"    Warning: Contents API failed for {text_name} page {page}: {e}")
                break
            if len(batch) < 1000:
                break
            time.sleep(0.4)

    # Parse filenames: TextName-NNNN-Citation, book, chapter-id.conllu
    # e.g. "Mahābhārata-0298-MBh, 3, 1-2454.conllu"
    # e.g. "Ṛgveda-0000-ṚV, 1, 1-9981.conllu"
    # e.g. "Hitopadeśa-0001-Hitop, 1-2247.conllu"
    mapping: dict[tuple[int, int], str] = {}
    for name in entries:
        if not name.endswith(".conllu") or name.endswith("_parsed.conllu"):
            continue
        # Extract citation part between second '-' and last '-'
        m = re.search(r"-(\d+)-(.+)-\d+\.conllu$", name)
        if not m:
            continue
        citation = m.group(2)  # e.g. "MBh, 3, 1" or "Hitop, 1" or "ṚV, 1, 1"
        parts = [p.strip() for p in citation.split(",")]
        if len(parts) >= 3:
            try:
                book, ch = int(parts[1]), int(parts[2])
                mapping[(book, ch)] = name
            except ValueError:
                pass
        elif len(parts) == 2:
            # texts with no "book" level (Hitopadeśa, Manu use "Hitop, 1")
            try:
                mapping[(0, int(parts[1]))] = name
            except ValueError:
                pass

    _DIR_CACHE[dcs_key] = mapping
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps([[list(k), v] for k, v in mapping.items()], ensure_ascii=False))
    print(f"    Cached {len(mapping)} chapter entries for {text_name}")
    return mapping


# ── HTTP / cache helpers ───────────────────────────────────────────────────────

def _fetch_conllu(dcs_key: str, filename: str) -> str:
    """Download a .conllu file, caching locally."""
    cache_path = CACHE_DIR / dcs_key / filename
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    text_name = DCS_DIR[dcs_key]
    url = f"{GITHUB_RAW}/{urllib.parse.quote(text_name, safe='')}/{urllib.parse.quote(filename, safe='')}"
    req = urllib.request.Request(url, headers={"User-Agent": "reshith-dcs/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            content = r.read().decode("utf-8")
    except Exception as e:
        print(f"    Error fetching {filename}: {e}")
        return ""
    cache_path.write_text(content, encoding="utf-8")
    time.sleep(0.2)
    return content


# ── CoNLL-U parser ────────────────────────────────────────────────────────────

def _parse_misc(misc: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if misc in ("_", ""):
        return result
    for item in misc.split("|"):
        if "=" in item:
            k, _, v = item.partition("=")
            result[k] = v
    return result


def _parse_feats(feats: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if feats in ("_", ""):
        return result
    for item in feats.split("|"):
        if "=" in item:
            k, _, v = item.partition("=")
            result[k] = v
    return result


def parse_conllu(content: str, chapter_ref: tuple[int, int] | None = None) -> list[dict]:
    """Parse a CoNLL-U file into a list of sentence dicts."""
    sentences: list[dict] = []
    current_meta: dict[str, str] = {}
    current_tokens: list[dict] = []
    current_ranges: dict[tuple[int, int], str] = {}  # (start,end) → sandhi form

    def flush():
        if not current_tokens:
            return
        # Build word list, collapsing range tokens into sandhi_groups
        words = []
        sandhi_groups: list[dict] = []

        # Map range spans to their surface form
        active_ranges: dict[int, tuple[int, str]] = {}  # start_i → (end_i, form)
        for (s, e), form in current_ranges.items():
            active_ranges[s] = (e, form)

        i = 0
        while i < len(current_tokens):
            tok = current_tokens[i]
            tok_id = tok["_id"]
            # Check if this token starts a sandhi range
            if tok_id in active_ranges:
                end_id, sandhi_form = active_ranges[tok_id]
                group_words = []
                j = i
                while j < len(current_tokens) and current_tokens[j]["_id"] <= end_id:
                    group_words.append(len(words) + (j - i))
                    j += 1
                # All words in this range
                group_start = len(words)
                for k in range(i, j):
                    words.append(current_tokens[k])
                sandhi_groups.append({"words": list(range(group_start, len(words))), "form": sandhi_form})
                i = j
            else:
                words.append(tok)
                i += 1

        sentences.append({
            "id": int(current_meta.get("sent_id", 0)),
            "text": current_meta.get("text", ""),
            "chapter": list(chapter_ref) if chapter_ref else None,
            "words": [{k: v for k, v in w.items() if not k.startswith("_")} for w in words],
            "sandhiGroups": sandhi_groups,
        })

    for line in content.splitlines():
        line = line.rstrip()

        if not line:
            flush()
            current_meta = {}
            current_tokens = []
            current_ranges = {}
            continue

        if line.startswith("## "):
            k, _, v = line[3:].partition(": ")
            current_meta[k.strip()] = v.strip()
            continue

        if line.startswith("# "):
            k, _, v = line[2:].partition(" = ")
            if v:
                current_meta[k.strip()] = v.strip()
            continue

        parts = line.split("\t")
        if len(parts) < 10:
            continue

        id_field = parts[0]

        # Range token (sandhi compound): "2-3"
        if "-" in id_field and not id_field.lstrip("-").isdigit():
            m = re.match(r"^(\d+)-(\d+)$", id_field)
            if m:
                s, e = int(m.group(1)), int(m.group(2))
                current_ranges[(s, e)] = parts[1]  # sandhi surface form
            continue

        # Skip decimal sub-tokens (0.1 etc.)
        try:
            tok_id = int(id_field)
        except ValueError:
            continue

        misc = _parse_misc(parts[9])
        feats = _parse_feats(parts[5])

        current_tokens.append({
            "_id": tok_id,
            "i": tok_id,
            "form": parts[1],
            "lemma": parts[2] if parts[2] != "_" else None,
            "upos": parts[3] if parts[3] != "_" else None,
            "feats": feats,
            "unsandhied": misc.get("Unsandhied") or parts[1],
            "lemmaId": int(misc["LemmaId"]) if "LemmaId" in misc else None,
        })

    flush()
    return sentences


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def fetch_chapters(dcs_key: str, book_chapters: list[tuple[int, int]]) -> list[dict]:
    """Fetch and parse a list of (book, chapter) pairs."""
    dir_map = _load_dir(dcs_key)
    all_sentences: list[dict] = []
    for bc in book_chapters:
        filename = dir_map.get(bc)
        if not filename:
            print(f"    Warning: no DCS file for {dcs_key} {bc}")
            continue
        content = _fetch_conllu(dcs_key, filename)
        if content:
            sents = parse_conllu(content, chapter_ref=bc)
            all_sentences.extend(sents)
    return all_sentences


def fetch_all_chapters(dcs_key: str) -> list[dict]:
    """Fetch all chapters for a text."""
    dir_map = _load_dir(dcs_key)
    # Sort by (book, chapter)
    sorted_keys = sorted(dir_map.keys())
    all_sentences: list[dict] = []
    for bc in sorted_keys:
        filename = dir_map[bc]
        content = _fetch_conllu(dcs_key, filename)
        if content:
            sents = parse_conllu(content, chapter_ref=bc)
            all_sentences.extend(sents)
    return all_sentences


# ── Output builders ───────────────────────────────────────────────────────────

def build_output(meta: dict, sentences: list[dict]) -> dict:
    return {**meta, "sentences": sentences}


def write_output(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    words = sum(len(s["words"]) for s in data["sentences"])
    print(f"    → {len(data['sentences'])} sentences, {words} words → {path.name}")


# ── Lanman selection targets ───────────────────────────────────────────────────
# Each entry: output_filename, description, fetch_spec
# fetch_spec: ("mbh"|"hitop"|"manu"|"rv", book_chapters_or_None)

TARGETS: list[tuple[str, dict, str, list[tuple[int, int]] | None]] = [
    # (output_stem, meta, dcs_key, book_chapters)

    # ── Mahābhārata Nalopākhyāna ───────────────────────────────────────────
    ("01", {
        "selectionNums": [1],
        "title": "Nala",
        "source": "Mahābhārata",
        "dcsText": "Mahābhārata",
        "note": "Nalopākhyāna = MBh 3.50–78",
    }, "mbh", [(3, ch) for ch in range(50, 79)]),

    # ── Hitopadeśa ────────────────────────────────────────────────────────
    ("hitopadesa", {
        "selectionNums": list(range(2, 22)),
        "title": "Hitopadeśa",
        "source": "Hitopadeśa",
        "dcsText": "Hitopadeśa",
        "note": "Books 0–4 (Lanman selections II–XXI)",
    }, "hitop", None),

    # ── Manu-smṛti ────────────────────────────────────────────────────────
    ("28", {
        "selectionNums": [28],
        "title": "Laws of Manu",
        "source": "Manusmṛti",
        "dcsText": "Manusmṛti",
        "note": "All 12 adhyāyas",
    }, "manu", None),

    # ── Ṛgveda — individual hymns ─────────────────────────────────────────
    # [?] marks uncertain assignments; verify against the physical book
    ("29", {"selectionNums": [29], "title": "Riddle of the Waters", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.164 [Asya vāmasya] [?]"},
     "rv", [(1, 164)]),
    ("30", {"selectionNums": [30], "title": "Riddle of the Year", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.164 (same as XXIX) [?]"},
     "rv", [(1, 164)]),
    ("31", {"selectionNums": [31], "title": "Hymn to Indra I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.32 [Vṛtra-slaying] [?]"},
     "rv", [(1, 32)]),
    ("32", {"selectionNums": [32], "title": "Hymn to Indra II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 2.12 [Yo jāta eva] [?]"},
     "rv", [(2, 12)]),
    ("33", {"selectionNums": [33], "title": "Hymn to Indra III", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.80 [?]"},
     "rv", [(1, 80)]),
    ("34", {"selectionNums": [34], "title": "Hymn to Indra IV", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 8.96 [?]"},
     "rv", [(8, 96)]),
    ("35", {"selectionNums": [35], "title": "Hymn to Agni I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.1 [Agnimīḷe]"},
     "rv", [(1, 1)]),
    ("36", {"selectionNums": [36], "title": "Hymn to Agni II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.26 [?]"},
     "rv", [(1, 26)]),
    ("37", {"selectionNums": [37], "title": "Hymn to Agni III", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 3.1 [?]"},
     "rv", [(3, 1)]),
    ("38", {"selectionNums": [38], "title": "Hymn to Agni IV", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 5.1 [?]"},
     "rv", [(5, 1)]),
    ("39", {"selectionNums": [39], "title": "Hymn to Soma", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 9.113 [?]"},
     "rv", [(9, 113)]),
    ("40", {"selectionNums": [40], "title": "Hymn to the Maruts", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.37 [?]"},
     "rv", [(1, 37)]),
    ("41", {"selectionNums": [41], "title": "Hymn to Varuṇa I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.86 [Varuṇa confession]"},
     "rv", [(7, 86)]),
    ("42", {"selectionNums": [42], "title": "Hymn to Varuṇa II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.87"},
     "rv", [(7, 87)]),
    ("43", {"selectionNums": [43], "title": "Hymn to Varuṇa III", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.88"},
     "rv", [(7, 88)]),
    ("44", {"selectionNums": [44], "title": "Hymn to Varuṇa IV", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.89"},
     "rv", [(7, 89)]),
    ("45", {"selectionNums": [45], "title": "Hymn to Varuṇa V", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.25 [?]"},
     "rv", [(1, 25)]),
    ("46", {"selectionNums": [46], "title": "Hymn to Viṣṇu", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.154 [Three strides]"},
     "rv", [(1, 154)]),
    ("47", {"selectionNums": [47], "title": "Dawn Hymn I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.113 [?]"},
     "rv", [(1, 113)]),
    ("48", {"selectionNums": [48], "title": "Dawn Hymn II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 6.64 [?]"},
     "rv", [(6, 64)]),
    ("49", {"selectionNums": [49], "title": "Dawn Hymn III", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.77 [?]"},
     "rv", [(7, 77)]),
    ("50", {"selectionNums": [50], "title": "Creation Hymn", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.129 [Nāsadīya sūkta]"},
     "rv", [(10, 129)]),
    ("51", {"selectionNums": [51], "title": "Purūravas and Urvaśī", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.95"},
     "rv", [(10, 95)]),
    ("52", {"selectionNums": [52], "title": "The Two Birds", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 1.164.20–22 (verses within XXIX) [?]"},
     "rv", [(1, 164)]),
    ("53", {"selectionNums": [53], "title": "Dialogue of Yama and Yamī", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.10"},
     "rv", [(10, 10)]),
    ("54", {"selectionNums": [54], "title": "The One Thing Needful", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.117 [?]"},
     "rv", [(10, 117)]),
    ("55", {"selectionNums": [55], "title": "Hymn of Man (Puruṣasūkta)", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.90"},
     "rv", [(10, 90)]),
    ("56", {"selectionNums": [56], "title": "Burial Hymn I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.14 [?]"},
     "rv", [(10, 14)]),
    ("57", {"selectionNums": [57], "title": "Burial Hymn II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.18 [?]"},
     "rv", [(10, 18)]),
    ("58", {"selectionNums": [58], "title": "Wedding Hymn I", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.85"},
     "rv", [(10, 85)]),
    ("59", {"selectionNums": [59], "title": "Wedding Hymn II", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.85 (same as LVIII) [?]"},
     "rv", [(10, 85)]),
    ("60", {"selectionNums": [60], "title": "Hymn to Night", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 10.127"},
     "rv", [(10, 127)]),
    ("61", {"selectionNums": [61], "title": "Hymn to the Frog", "source": "Ṛgveda",
            "dcsText": "Ṛgveda", "note": "RV 7.103"},
     "rv", [(7, 103)]),
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    # Determine which targets to process
    if not args:
        targets = TARGETS
    else:
        selected: list = []
        for a in args:
            if a.isdigit():
                num = int(a)
                t = [t for t in TARGETS if num in t[1].get("selectionNums", [])]
                selected.extend(t)
            else:
                t = [t for t in TARGETS if a.lower() in t[0].lower()]
                selected.extend(t)
        # Deduplicate preserving order
        seen: set[str] = set()
        targets = []
        for t in selected:
            if t[0] not in seen:
                seen.add(t[0])
                targets.append(t)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for stem, meta, dcs_key, book_chapters in targets:
        print(f"\n{stem}: {meta['title']} ({meta['note']})")
        if book_chapters is not None:
            sentences = fetch_chapters(dcs_key, book_chapters)
        else:
            sentences = fetch_all_chapters(dcs_key)
        data = build_output(meta, sentences)
        write_output(OUTPUT_DIR / f"{stem}.json", data)

    print("\nDone.")


if __name__ == "__main__":
    main()
