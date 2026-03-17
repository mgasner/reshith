#!/usr/bin/env python3
"""
Produce a reviewable index of story openings in the DCS Hitopadeśa data.

For each candidate story start (asti/āsīt/purā sentences + GRETIL kathā labels),
prints the DCS sentence ID, book, opening sentence, and 8 sentences of context.

Usage:
    python data/sanskrit/analyze_hitop.py
    python data/sanskrit/analyze_hitop.py 2   # book 2 only
"""

import json
import re
import sys
from pathlib import Path

DCS_PATH  = Path(__file__).parents[2] / "frontend/public/data/sanskrit/lanman/hitopadesa.json"
GRETIL_PATH = Path(__file__).parent / "dcs_cache/hitopadesa_gretil.txt"

CONTEXT_SENTENCES = 8

# ── Load DCS sentences ────────────────────────────────────────────────────────

data  = json.loads(DCS_PATH.read_text())
sents = data["sentences"]

# Build (book → ordered sentence list) and (sent_id → index)
by_book: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
id_to_idx: dict[int, int] = {}
for idx, s in enumerate(sents):
    id_to_idx[s["id"]] = idx
    ch = s.get("chapter")
    if ch and ch[1] in by_book:
        by_book[ch[1]].append(s)

# ── Parse GRETIL kathā labels ─────────────────────────────────────────────────

def parse_gretil_kathas(text: str) -> list[dict]:
    """Return list of {book, label, verse_start, prose_opening}."""
    lines  = text.splitlines()
    results = []
    current_book = 0
    book_map = {"i": 1, "ii": 2, "iii": 3, "iv": 4}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        bm = re.match(r"^(i{1,4}v?)\.\s+\S", line, re.I)
        if bm:
            current_book = book_map.get(bm.group(1).lower(), 0)
            i += 1
            continue
        km = re.match(r"^(kathā\s*\d+\w*)", line, re.I)
        if km:
            label = km.group(1)
            # First prose after label
            prose = ""
            j = i + 1
            while j < len(lines):
                c = lines[j].strip()
                if c and "//" not in c and len(c) > 10:
                    prose = c
                    break
                j += 1
            # First verse ref after label
            verse = None
            j = i + 1
            while j < min(i + 25, len(lines)):
                vm = re.search(r"// (\S+_\d+\.\d+) //", lines[j])
                if vm:
                    verse = vm.group(1)
                    break
                j += 1
            results.append({"book": current_book, "label": label,
                            "verse": verse, "prose": prose})
        i += 1
    return results

gretil_kathas = parse_gretil_kathas(GRETIL_PATH.read_text())

# Map GRETIL prose opening → kathā label (first ~40 chars, normalized)
def normalize(s: str) -> str:
    return re.sub(r"[\s\-–—]+", "", s.lower())[:40]

gretil_map: dict[str, str] = {
    normalize(k["prose"]): f"{k['label']} (hit {k['verse'] or '?'})"
    for k in gretil_kathas
}

# ── Identify story-opening sentences ─────────────────────────────────────────

OPENER_RE = re.compile(r"^(asti|āsīt|asty|purā)\b", re.I)
FRAME_OPENERS = {
    # Book frame openings (not asti-pattern but important landmarks)
    351382: "B1 FRAME — four friends: crow sees hunter",
    352283: "B2 FRAME — princes ask for suhṛdbheda",
    353157: "B3 FRAME — princes ask for vigraha",
    353993: "B4 FRAME — princes ask for sandhi",
}

candidates: list[dict] = []
seen_ids: set[int] = set()

# Frame openers
for sid, note in FRAME_OPENERS.items():
    idx = id_to_idx.get(sid)
    if idx is not None:
        s = sents[idx]
        candidates.append({"sent": s, "idx": idx, "note": note, "gretil": ""})
        seen_ids.add(sid)

# asti/āsīt/purā sentence openers
for idx, s in enumerate(sents):
    if s["id"] in seen_ids:
        continue
    ch = s.get("chapter")
    if not ch:
        continue
    txt = s["text"]
    if OPENER_RE.match(txt):
        norm = normalize(txt)
        gretil_label = gretil_map.get(norm, "")
        candidates.append({"sent": s, "idx": idx, "note": "", "gretil": gretil_label})
        seen_ids.add(s["id"])

# Sort by position in corpus
candidates.sort(key=lambda c: c["idx"])

# ── Filter by book if requested ───────────────────────────────────────────────

target_book = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if target_book:
    candidates = [c for c in candidates
                  if c["sent"].get("chapter") and c["sent"]["chapter"][1] == target_book]

# ── Print ─────────────────────────────────────────────────────────────────────

BOOK_NAMES = {0: "Intro", 1: "Mitralābha", 2: "Suhṛdbheda", 3: "Vigraha", 4: "Sandhi"}

current_book_printed = -1

for c in candidates:
    s     = c["sent"]
    idx   = c["idx"]
    book  = s["chapter"][1] if s.get("chapter") else 0
    sid   = s["id"]

    # Book header
    if book != current_book_printed:
        print()
        print("=" * 72)
        print(f"  BOOK {book}: {BOOK_NAMES.get(book, '?')}")
        print("=" * 72)
        current_book_printed = book

    # Story header
    gretil_tag = f"  [GRETIL: {c['gretil']}]" if c["gretil"] else ""
    note_tag   = f"  ** {c['note']} **" if c["note"] else ""
    print()
    print(f"  ── sent_id {sid}  (book {book}){gretil_tag}{note_tag}")
    print(f"  OPEN: {s['text'][:90]}")

    # Context: next CONTEXT_SENTENCES sentences
    for j in range(idx + 1, min(idx + 1 + CONTEXT_SENTENCES, len(sents))):
        ns = sents[j]
        # Stop at next book boundary
        nch = ns.get("chapter")
        if nch and nch[1] != book:
            print(f"  --- (book boundary) ---")
            break
        words_preview = " ".join(w["form"] for w in ns["words"][:12])
        flag = " ◀ NEXT STORY?" if OPENER_RE.match(ns["text"]) else ""
        print(f"  {ns['id']}  {words_preview[:75]}{flag}")

print()
print(f"Total candidates: {len(candidates)}")
