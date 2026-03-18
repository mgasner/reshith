#!/usr/bin/env python3
"""
Build a Monier-Williams lexicon for every lemma that appears in Lanman's
Sanskrit Reader DCS data files.

Source: Cologne Digital Sanskrit Dictionaries — Monier-Williams (1899, public domain)
Data:   https://raw.githubusercontent.com/sanskrit-lexicon/csl-orig/master/v02/mw/mw.txt

One-time download (50 MB):
  curl -L -o data/sanskrit/mw.txt \
    https://raw.githubusercontent.com/sanskrit-lexicon/csl-orig/master/v02/mw/mw.txt

Output: frontend/public/data/sanskrit/lanman_lexicon.json
  {lemma_iast: {hw: str, gloss: str}, ...}

Usage:
  python data/sanskrit/build_lanman_lexicon.py            # full build
  python data/sanskrit/build_lanman_lexicon.py --dry-run  # list lemmas only
"""

import html
import json
import re
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

LANMAN_DIR = Path(__file__).parents[2] / "frontend" / "public" / "data" / "sanskrit" / "lanman"
MW_FILE    = Path(__file__).parent / "mw.txt"
OUTPUT     = LANMAN_DIR.parent / "lanman_lexicon.json"

# ── IAST ↔ SLP1 transliteration ───────────────────────────────────────────────

_IAST_SLP1: list[tuple[str, str]] = [
    # Vowels
    ("ā", "A"), ("Ā", "A"),
    ("ī", "I"), ("Ī", "I"),
    ("ū", "U"), ("Ū", "U"),
    ("ṝ", "F"), ("ṛ", "f"),
    ("ḷ", "x"),
    ("ai", "E"),
    ("au", "O"),
    # Anusvara / visarga
    ("ṃ", "M"), ("ṁ", "M"),
    ("ḥ", "H"),
    # Aspirated stops — must come BEFORE their unaspirated bases
    ("kh", "K"), ("gh", "G"),
    ("ch", "C"),
    ("jh", "J"),
    ("ṭh", "W"), ("Ṭh", "W"),
    ("ḍh", "Q"), ("Ḍh", "Q"),
    ("th", "T"),
    ("dh", "D"),
    ("ph", "P"),
    ("bh", "B"),
    # Nasals with diacritics
    ("ṅ", "N"),
    ("ñ", "Y"),
    ("ṇ", "R"),
    # Retroflexes
    ("ṭ", "w"), ("Ṭ", "w"),
    ("ḍ", "q"), ("Ḍ", "q"),
    # Sibilants
    ("ś", "S"), ("Ś", "S"),
    ("ṣ", "z"), ("Ṣ", "z"),
]

_SLP1_IAST: list[tuple[str, str]] = [
    ("A", "ā"), ("I", "ī"), ("U", "ū"),
    ("F", "ṝ"), ("f", "ṛ"), ("x", "ḷ"),
    ("E", "ai"), ("O", "au"),
    ("M", "ṃ"), ("H", "ḥ"),
    # Aspirated stops (before unaspirated so K→kh not k+h)
    ("K", "kh"), ("G", "gh"),
    ("C", "ch"),
    ("J", "jh"),
    ("W", "ṭh"), ("Q", "ḍh"),
    ("T", "th"), ("D", "dh"),
    ("P", "ph"), ("B", "bh"),
    ("N", "ṅ"), ("Y", "ñ"),
    ("w", "ṭ"), ("q", "ḍ"), ("R", "ṇ"),
    ("S", "ś"), ("z", "ṣ"),
]


def iast_to_slp1(text: str) -> str:
    for src, dst in _IAST_SLP1:
        text = text.replace(src, dst)
    return text


def slp1_to_iast(text: str) -> str:
    for src, dst in _SLP1_IAST:
        text = text.replace(src, dst)
    return text


# ── Parse mw.txt ──────────────────────────────────────────────────────────────
# Format (3 lines per entry):
#   <L>N<pc>p<k1>SLP1KEY<k2>...<h>N<e>type
#   body text with XML-like tags
#   <LEND>

_K1_RE    = re.compile(r"<k1>([^<]+)")
_ETYPE_RE = re.compile(r"<e>([^<]+)")  # entry type: 1, 2, 2A, 2B, …
_TAG_RE   = re.compile(r"<[^>]+>")
_WS_RE    = re.compile(r"\s+")
_SAN_RE   = re.compile(r"<s>([^<]+)</s>")         # SLP1 Sanskrit: decode
_S1_RE    = re.compile(r"<s\d[^>]*>[^<]*</s\d[^>]*>")  # proper names: strip
_LEX_RE   = re.compile(r"<lex[^>]*>([^<]+)</lex>", re.IGNORECASE)
# MW uses ¦ (broken bar, U+00A6) to separate headword metadata from definition
_DEF_SEP  = "\u00a6"


def _strip_inner(tag_content: str) -> str:
    """Strip inner tags from a <s> block before SLP1 decoding."""
    return _TAG_RE.sub("", tag_content)


def _decode_body(raw: str) -> str:
    """Decode MW markup to plain unicode text."""
    text = html.unescape(raw)
    if _DEF_SEP in text:
        text = text[text.index(_DEF_SEP) + 1:]
    text = _S1_RE.sub("", text)
    text = re.sub(r"<s>(.*?)</s>",
                  lambda m: slp1_to_iast(_strip_inner(m.group(1))), text)
    text = _LEX_RE.sub(lambda m: m.group(1), text)
    text = _TAG_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


_ENGLISH_WORD_RE = re.compile(r"\b(a|an|the|to|of|one|used|name|kind|sort|class|any|also|"
                               r"form|place|time|way|part|person|thing|being|state|act|"
                               r"belonging|relating|applied|called|denoting|meaning)\b")


def _skip_balanced(text: str) -> str:
    """Skip one leading balanced parenthetical group. Returns rest of string."""
    text = text.lstrip()
    if not text.startswith("("):
        return text
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:].lstrip()
    return text  # unbalanced


def _trim_clause(text: str) -> str:
    """Take first sense: cut at first ; then limit to 4 commas."""
    text = text.split(";")[0]
    parts = text.split(",")
    if len(parts) > 4:
        text = ",".join(parts[:4])
    return text.strip().rstrip(",.;").strip()


def _looks_english(s: str) -> bool:
    """True if s starts with an English-looking lowercase word/phrase."""
    if not s:
        return False
    # Must start with a lowercase alphabetic character
    if not s[0].isalpha() or not s[0].islower():
        return False
    # Reject single-char grammar abbreviations like "f(" or "m(" or "n."
    if len(s) < 4:
        return False
    # Reject things like "f(-rājan" or "n. " (grammar markers)
    if re.match(r"^[mfn]\s*[.((/]", s):
        return False
    return True


def _extract_gloss(text: str) -> str:
    """Try to pull an English definition from a decoded MW body."""
    # Strategy 1: find the last occurrence of ") [English word]" in the text
    # MW grammar notes end with ")" and the definition follows
    for m in reversed(list(re.finditer(r"\)\s+([a-z])", text))):
        candidate = text[m.start(1):]
        if _looks_english(candidate[:20]):
            result = _trim_clause(candidate)
            if len(result) > 8:
                return result

    # Strategy 2: skip lex-category prefix and a balanced parenthetical
    text2 = re.sub(r"^\s*[mfn][a-z()/.,\s]*\.\s*", "", text)
    text2 = _skip_balanced(text2)
    text2 = _skip_balanced(text2)  # sometimes two layers
    if _looks_english(text2[:30]):
        result = _trim_clause(text2)
        if len(result) > 4:
            return result

    # Strategy 3: find first "; [English phrase]" after the header
    for m in re.finditer(r";\s+([a-z][a-z ]+)", text):
        candidate = text[m.start(1):]
        if _looks_english(candidate[:30]):
            result = _trim_clause(candidate)
            if len(result) > 8:
                return result

    # Fallback: return the whole first clause
    return _trim_clause(text)


def clean_body(raw: str) -> str:
    """Extract a short, readable gloss from a MW body line."""
    text = _decode_body(raw)
    gloss = _extract_gloss(text)
    # Remove trailing citation fragments like "RV." or "MBh."
    gloss = re.sub(r",?\s+[A-Z][A-Za-z.&\s]{0,12}\.?\s*$", "", gloss).strip()
    if len(gloss) > 140:
        gloss = gloss[:137].rsplit(" ", 1)[0] + "…"
    return gloss


def load_mw_index(lemma_slp1_set: set[str]) -> dict[str, dict]:
    """
    Parse mw.txt and return {slp1_key: {primary: str, subs: [str, ...]}}
    for keys in lemma_slp1_set.
    """
    index: dict[str, dict] = {}
    print(f"Parsing {MW_FILE} …", flush=True)

    with open(MW_FILE, encoding="utf-8") as fh:
        header = None
        body_lines: list[str] = []
        for line in fh:
            line = line.rstrip("\n")
            if line == "<LEND>":
                if header and body_lines:
                    k1_m = _K1_RE.search(header)
                    et_m = _ETYPE_RE.search(header)
                    if k1_m and k1_m.group(1) in lemma_slp1_set:
                        k1    = k1_m.group(1)
                        etype = et_m.group(1) if et_m else ""
                        gloss = clean_body(" ".join(body_lines))
                        if gloss:
                            if k1 not in index:
                                index[k1] = {"primary": "", "subs": []}
                            is_sub = bool(re.search(r"[A-Z]", etype))  # e.g. 2A, 2B
                            if not is_sub and not index[k1]["primary"]:
                                index[k1]["primary"] = gloss
                            elif is_sub:
                                index[k1]["subs"].append(gloss)
                header = None
                body_lines = []
            elif header is None:
                header = line
            else:
                body_lines.append(line)

    print(f"  {len(index)} matching entries found", flush=True)
    return index


# ── Collect unique lemmas from all lanman/*.json ───────────────────────────────

def collect_lemmas() -> set[str]:
    lemmas: set[str] = set()
    for path in sorted(LANMAN_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        for sent in data.get("sentences", []):
            for word in sent.get("words", []):
                lemma = word.get("lemma")
                if lemma and lemma != "_":
                    lemmas.add(lemma)
    return lemmas


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not MW_FILE.exists():
        print(f"ERROR: {MW_FILE} not found.")
        print("Download it with:")
        print("  curl -L -o data/sanskrit/mw.txt \\")
        print("    https://raw.githubusercontent.com/sanskrit-lexicon/csl-orig/master/v02/mw/mw.txt")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv

    print("Collecting lemmas from lanman/*.json …", flush=True)
    lemmas = collect_lemmas()
    print(f"  {len(lemmas)} unique lemmas found", flush=True)

    if dry_run:
        for lm in sorted(lemmas):
            print(f"  {lm}")
        return

    # Build SLP1 → IAST mapping (for re-labelling results)
    slp1_to_iast_map: dict[str, str] = {iast_to_slp1(lm): lm for lm in lemmas}
    lemma_slp1_set = set(slp1_to_iast_map)

    # Parse MW and build index for only our lemmas
    mw_index = load_mw_index(lemma_slp1_set)

    # Build lexicon
    lexicon: dict[str, dict] = {}
    missing: list[str] = []

    for lm in sorted(lemmas):
        slp1  = iast_to_slp1(lm)
        entry = mw_index.get(slp1)

        if entry:
            # Prefer sub-entry if primary gloss starts with grammar noise
            primary = entry["primary"]
            subs    = entry["subs"]
            # A "good" gloss starts with a lowercase English word, not grammar tags
            def looks_english(s: str) -> bool:
                return bool(s) and s[0].islower() and not s.startswith(("m.", "f.", "n.", "mf"))
            gloss = primary
            if not looks_english(primary) and subs:
                gloss = next((s for s in subs if looks_english(s)), primary)
            lexicon[lm] = {"hw": slp1_to_iast(slp1), "gloss": gloss}
        else:
            # Fallback: try stem without final -a (common nominal stem variation)
            stem = slp1.rstrip("a")
            if stem and stem != slp1:
                entry2 = mw_index.get(stem)
                if entry2:
                    primary2 = entry2["primary"]
                    subs2    = entry2["subs"]
                    def looks_english2(s: str) -> bool:
                        return bool(s) and s[0].islower() and not s.startswith(("m.", "f.", "n.", "mf"))
                    gloss2 = primary2
                    if not looks_english2(primary2) and subs2:
                        gloss2 = next((s for s in subs2 if looks_english2(s)), primary2)
                    lexicon[lm] = {"hw": slp1_to_iast(stem), "gloss": gloss2}
                    continue
            missing.append(lm)

    print(f"  {len(lexicon)} lemmas matched,  {len(missing)} unmatched", flush=True)

    OUTPUT.write_text(json.dumps(lexicon, ensure_ascii=False, indent=2))
    print(f"Wrote {len(lexicon)} entries → {OUTPUT}", flush=True)

    if missing:
        sample = ", ".join(missing[:25]) + (" …" if len(missing) > 25 else "")
        print(f"Unmatched ({len(missing)}): {sample}")


if __name__ == "__main__":
    main()
