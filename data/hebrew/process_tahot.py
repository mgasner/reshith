#!/usr/bin/env python3
"""
Process STEPBible TAHOT files into a frequency list JSON.

Column layout (0-indexed, tab-separated):
  0  Eng (Heb) Ref & Type   e.g. Gen.1.1#01=L
  1  Hebrew                 full pointed text w/ prefix/suffix slashes
  2  Transliteration
  3  Translation            slash-separated gloss for prefix/root/suffix
  4  dStrongs               e.g. H9003/{H1254A}  root in {curly braces}
  5  Grammar
  6  Meaning Variants
  7  Spelling Variants
  8  Root dStrong+Instance  e.g. H1254A  (root strong's, may have _A/_B instance suffix)
  9  Alternative Strongs+Instance
 10  Conjoin word
 11  Expanded Strong tags   e.g. {H1254A=בָּרָא=to create}
"""

import json
import os
import re
from collections import defaultdict, Counter

INPUT_FILES = [
    "/Users/max/dev/reshith/data/hebrew/tahot_raw/TAHOT_Gen-Deu.txt",
    "/Users/max/dev/reshith/data/hebrew/tahot_raw/TAHOT_Jos-Est.txt",
    "/Users/max/dev/reshith/data/hebrew/tahot_raw/TAHOT_Job-Sng.txt",
    "/Users/max/dev/reshith/data/hebrew/tahot_raw/TAHOT_Isa-Mal.txt",
]

OUTPUT_FILE = "/Users/max/dev/reshith/data/hebrew/frequency.json"

# Grammar prefix -> part of speech label
GRAMMAR_POS = {
    "HVq": "verb",
    "HVn": "verb",
    "HVp": "verb",
    "HVh": "verb",
    "HVt": "verb",
    "HVi": "verb",
    "HVc": "verb",
    "HVj": "verb",
    "HVw": "verb",
    "HVr": "verb",
    "HNc": "noun",
    "HNp": "proper noun",
    "HTd": "article",
    "HTo": "particle",  # object marker
    "HR":  "preposition",
    "HC":  "conjunction",
    "Hc":  "conjunction",
    "HT":  "particle",
    "HM":  "number",
    "HDs": "pronoun",  # demonstrative
    "HDp": "pronoun",  # demonstrative
    "HPp": "pronoun",  # personal
    "HPr": "pronoun",  # personal
    "HI":  "interjection",
    "HE":  "exclamation",
    "HNr": "proper noun",
}

def parse_pos(grammar_code: str) -> str:
    """Map ETCBC-style grammar code to a human-readable POS label."""
    # grammar_code may be slash-joined for prefix/root/suffix, take root part
    # e.g. "HR/Ncfsa" -> look at "HNc..." part for noun
    # We want the dominant (root) POS.
    parts = grammar_code.split("/")
    for part in parts:
        part = part.strip()
        # Try progressively shorter prefixes
        for length in (4, 3, 2):
            prefix = part[:length]
            if prefix in GRAMMAR_POS:
                return GRAMMAR_POS[prefix]
        # Single-char type codes after "H" prefix
        if part.startswith("H") and len(part) >= 2:
            code = part[1]
            mapping = {
                "V": "verb",
                "N": "noun",
                "T": "particle",
                "R": "preposition",
                "C": "conjunction",
                "M": "number",
                "D": "pronoun",
                "P": "pronoun",
                "I": "interjection",
                "E": "exclamation",
            }
            if code in mapping:
                return mapping[code]
    return "unknown"


def extract_root_strongs(dstrongs: str) -> str:
    """Extract root Strong's number from dStrongs field.
    Root is in {curly braces}.  Returns first root found, or first tag overall.
    e.g. 'H9003/{H7225G}' -> 'H7225G'
         '{H1254A}'        -> 'H1254A'
    """
    m = re.search(r'\{(H\d+[A-Z]*)\}', dstrongs)
    if m:
        return m.group(1)
    # Fallback: first H-tag in string
    m = re.search(r'(H\d+[A-Z]*)', dstrongs)
    if m:
        return m.group(1)
    return ""


def extract_lemma_and_gloss_from_expanded(expanded: str):
    """
    Parse column 11 (Expanded Strong tags) to get the lemma Hebrew form and gloss
    for the root word.

    Format: {H1254A=בָּרָא=to create}
    or with sub-meaning: {H0776G=אֶ֫רֶץ=: country;_planet»land:2_country;_planet}

    Returns (hebrew_lemma, gloss) for the root (curly-brace) entry, or ("", "").
    """
    # Find the root entry in curly braces
    m = re.search(r'\{(H\d+[A-Z]*)=([^=}]+)=([^}]+)\}', expanded)
    if m:
        lemma_hebrew = m.group(2).strip()
        raw_gloss = m.group(3).strip()
        # Clean gloss: take part before » or after : prefix
        # e.g. ": country;_planet»land:2_country;_planet" -> "country"
        # e.g. "to create" -> "to create"
        # e.g. ": beginning»first:1_beginning" -> "beginning"
        gloss = raw_gloss
        # Remove leading colon and space
        gloss = re.sub(r'^:\s*', '', gloss)
        # Take part before »
        gloss = gloss.split('»')[0].strip()
        # Remove trailing semicolons and underscored alternatives
        gloss = gloss.split(';')[0].strip()
        # Replace underscores with spaces
        gloss = gloss.replace('_', ' ').strip()
        # Remove <angle brackets> markers
        gloss = re.sub(r'[<\[\]>]', '', gloss).strip()
        return lemma_hebrew, gloss
    return "", ""


def strip_to_consonants(hebrew: str) -> str:
    """
    Remove niqqud (vowel points), cantillation marks, and other diacritics,
    keeping only Hebrew consonants and basic punctuation (maqaf, sof pasuq).
    Also strip prefix/suffix separators (/ and \).
    """
    result = []
    for ch in hebrew:
        cp = ord(ch)
        # Hebrew letters: U+05D0–U+05EA
        if 0x05D0 <= cp <= 0x05EA:
            result.append(ch)
        # Hebrew punctuation we want to keep: maqaf U+05BE, sof pasuq U+05C3
        # (we skip these for the lemma form)
    return ''.join(result)


def parse_transliteration_root(translit: str) -> str:
    """Extract root transliteration (between slashes if present)."""
    parts = translit.split('/')
    # Root is the last non-empty slash-separated segment that is not a prefix particle
    for part in reversed(parts):
        part = part.strip()
        if part:
            return part
    return translit.strip()


def is_data_row(ref: str) -> bool:
    """Return True if the reference field looks like a real data row."""
    # Must match pattern like Gen.1.1#01=L
    return bool(re.match(r'^[A-Z1-9][a-zA-Z0-9]+\.\d+\.\d+#\d+', ref))


def process_files():
    # lemma_data[root_strongs] = {
    #   "hebrew_forms": Counter of Hebrew consonant forms
    #   "glosses": Counter of glosses
    #   "pos_codes": Counter of grammar codes
    #   "translits": Counter of transliterations
    #   "count": int
    # }
    lemma_data = defaultdict(lambda: {
        "hebrew_forms": Counter(),
        "glosses": Counter(),
        "pos_codes": Counter(),
        "translits": Counter(),
        "count": 0,
    })

    total_rows = 0
    skipped = 0

    for filepath in INPUT_FILES:
        print(f"Processing {os.path.basename(filepath)} ...")
        past_header = False
        with open(filepath, encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.rstrip('\n')

                # Skip comment/header/blank lines
                if not line or line.startswith('#') or line.startswith('\t'):
                    continue
                if line.startswith('Eng (Heb) Ref'):
                    past_header = True
                    continue
                if not past_header:
                    continue

                parts = line.split('\t')
                if len(parts) < 9:
                    continue

                ref       = parts[0].strip()
                hebrew    = parts[1].strip()
                translit  = parts[2].strip()
                gloss_raw = parts[3].strip()
                dstrongs  = parts[4].strip()
                grammar   = parts[5].strip()
                expanded  = parts[11].strip() if len(parts) > 11 else ""

                if not is_data_row(ref):
                    skipped += 1
                    continue

                # Extract root Strong's
                root_strongs = extract_root_strongs(dstrongs)
                if not root_strongs:
                    skipped += 1
                    continue

                total_rows += 1

                entry = lemma_data[root_strongs]
                entry["count"] += 1

                # Hebrew consonant form from Expanded tags (lemma form, unpointed)
                lemma_heb, lemma_gloss = extract_lemma_and_gloss_from_expanded(expanded)

                if lemma_heb:
                    consonant_form = strip_to_consonants(lemma_heb)
                else:
                    consonant_form = strip_to_consonants(hebrew)

                if consonant_form:
                    entry["hebrew_forms"][consonant_form] += 1

                # Gloss: prefer expanded tag gloss, fall back to Translation column
                if lemma_gloss:
                    gloss = lemma_gloss
                else:
                    # Translation column has slash-separated parts; take the root part
                    gloss_parts = gloss_raw.split('/')
                    gloss = gloss_parts[-1].strip() if gloss_parts else gloss_raw
                    # Clean angle/square brackets
                    gloss = re.sub(r'[<\[\]>]', '', gloss).strip()

                if gloss:
                    entry["glosses"][gloss] += 1

                # Grammar / POS
                if grammar:
                    entry["pos_codes"][grammar] += 1

                # Transliteration (root part only)
                root_translit = parse_transliteration_root(translit)
                if root_translit:
                    entry["translits"][root_translit] += 1

    print(f"Total word tokens processed: {total_rows}")
    print(f"Unique lemmas (root Strong's): {len(lemma_data)}")

    # Build output entries
    entries = []
    for strongs, data in lemma_data.items():
        count = data["count"]
        if count == 0:
            continue

        # Most common Hebrew consonant form
        hebrew_form = data["hebrew_forms"].most_common(1)[0][0] if data["hebrew_forms"] else ""

        # Most common gloss
        gloss = data["glosses"].most_common(1)[0][0] if data["glosses"] else ""

        # Most common grammar code -> POS
        top_grammar = data["pos_codes"].most_common(1)[0][0] if data["pos_codes"] else ""
        pos = parse_pos(top_grammar)

        # Most common transliteration
        top_translit = data["translits"].most_common(1)[0][0] if data["translits"] else ""

        # Normalise Strong's: strip instance suffix (e.g. H1254A -> H1254A, H0853_A -> H0853)
        # Keep disambiguating letter (A/B/C/G etc. that's part of the base tag) but strip _A/_B instance
        clean_strongs = re.sub(r'_[A-Z]$', '', strongs)

        entries.append({
            "hebrew": hebrew_form,
            "strongs": clean_strongs,
            "transliteration": top_translit,
            "gloss": gloss,
            "part_of_speech": pos,
            "frequency": count,
        })

    # Sort by frequency descending
    entries.sort(key=lambda x: x["frequency"], reverse=True)

    output = {
        "source": "STEPBible TAHOT",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": (
            "Data created by STEPBible.org based on work at Tyndale House Cambridge. "
            "https://github.com/STEPBible/STEPBible-Data"
        ),
        "description": (
            "Hebrew Old Testament word frequency list derived from the Translators "
            "Amalgamated Hebrew OT (TAHOT), which tags every word of the Leningrad "
            "Codex with disambiguated Strong's numbers, ETCBC morphology, and "
            "English glosses. Entries are grouped by root lemma (disambiguated "
            "Strong's number) and sorted by total occurrence count."
        ),
        "total_entries": len(entries),
        "entries": entries,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Written {len(entries)} entries to {OUTPUT_FILE}")

    # Print top 20 for verification
    print("\nTop 20 entries:")
    for e in entries[:20]:
        print(f"  {e['frequency']:6d}  {e['hebrew']:20s}  {e['strongs']:10s}  {e['gloss']:30s}  {e['part_of_speech']}")


if __name__ == "__main__":
    process_files()
