"""
Build frontend/public/data/old_english/beowulf.json from public-domain sources.

Sources:
  OE text  — Beowulf (Harrison and Sharp), Wikisource
              https://en.wikisource.org/wiki/Beowulf_(Harrison_and_Sharp)
  Translation — J. Lesslie Hall (1892), Project Gutenberg #16328

Run from repo root:
    python data/old_english/process_beowulf.py

Output:
    frontend/public/data/old_english/beowulf.json
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

OUT = Path(__file__).parent.parent.parent / "frontend/public/data/old_english/beowulf.json"

WIKISOURCE_API = (
    "https://en.wikisource.org/w/api.php"
    "?action=query&titles=Beowulf+(Harrison+and+Sharp)"
    "&prop=revisions&rvprop=content&format=json&rvslots=main"
)

GUTENBERG_HALL = "https://www.gutenberg.org/cache/epub/16328/pg16328.txt"

UA = "Mozilla/5.0 (compatible; reshith-build/1.0)"

FITTS = [
    ("I",       "The Spear-Danes",               1,    52),
    ("II",      "Heorot",                        53,   114),
    ("III",     "Grendel's Ravages",             115,  193),
    ("IV",      "Beowulf Sets Sail",             194,  257),
    ("V",       "Arrival in Denmark",            258,  319),
    ("VI",      "The Hall-Watching",             320,  370),
    ("VII",     "Unferth's Challenge",           371,  455),
    ("VIII",    "Beowulf's Reply",               456,  498),
    ("IX",      "The Feast",                     499,  558),
    ("X",       "Night Watch",                   559,  661),
    ("XI",      "Grendel Comes",                 662,  709),
    ("XII",     "The Battle",                    710,  790),
    ("XIII",    "The Victory",                   791,  836),
    ("XIV",     "The Morning After",             837,  924),
    ("XV",      "The Celebration",               925,  990),
    ("XVI",     "Hrothgar's Gift",               991,  1049),
    ("XVII",    "The Scop's Tale of Finnsburg", 1050,  1124),
    ("XVIII",   "The Queen's Cup",              1125,  1191),
    ("XIX",     "More Gifts",                   1192,  1250),
    ("XX",      "Grendel's Mother Attacks",     1251,  1320),
    ("XXI",     "The Second Attack",            1321,  1382),
    ("XXII",    "The Mere",                     1383,  1472),
    ("XXIII",   "Descent into the Mere",        1473,  1556),
    ("XXIV",    "Battle in the Mere",           1557,  1650),
    ("XXV",     "The Sword",                    1651,  1739),
    ("XXVI",    "Return to Heorot",             1740,  1802),
    ("XXVII",   "More Counsel",                 1803,  1887),
    ("XXVIII",  "Homeward Bound",               1888,  1962),
    ("XXIX",    "Return to Geatland",           1963,  2038),
    ("XXX",     "Ingeld's Story",               2039,  2143),
    ("XXXI",    "The Treasures",                2144,  2220),
    ("XXXII",   "The Dragon",                   2221,  2311),
    ("XXXIII",  "The Hoard",                    2312,  2390),
    ("XXXIV",   "The Dragon Wakes",             2391,  2459),
    ("XXXV",    "Beowulf Prepares",             2460,  2601),
    ("XXXVI",   "The Battle Begins",            2602,  2693),
    ("XXXVII",  "Wiglaf",                       2694,  2820),
    ("XXXVIII", "The Dragon Slain",             2821,  2891),
    ("XXXIX",   "Beowulf's Death",              2892,  2945),
    ("XL",      "Wiglaf's Lament",              2946,  3057),
    ("XLI",     "The Messenger",               3058,  3075),
    ("XLII",    "The Funeral Pyre",            3076,  3136),
    ("XLIII",   "The Barrow",                  3137,  3182),
]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def clean_word(s: str) -> str:
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\{\{[^}]*\}\}', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r"'''?|''?", '', s)
    s = s.replace('\u00ad', '').replace('\u2010', '').replace('\u2013', '')
    return ' '.join(s.split()).strip()


def parse_oe_wikitext(wikitext: str) -> dict[int, tuple[str, str]]:
    start = wikitext.find('Hwæt')
    if start == -1:
        start = 0
    poem_body = wikitext[start:]

    lines_out: dict[int, tuple[str, str]] = {}
    line_num = 0

    for raw in poem_body.split('\n'):
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith('=') or raw.startswith('{|') or raw.startswith('|}'):
            continue
        # Skip pure template lines that aren't poem lines
        if re.match(r'^\{\{(?!gap|pline|anchor)[^}]+\}\}$', raw):
            continue

        # Extract explicit line numbers
        pline_m = re.search(r'\{\{pline\|(\d+)\}\}', raw)
        anchor_m = re.search(r'\{\{anchor\|l(\d+)\}\}', raw)
        explicit_num = None
        if pline_m:
            explicit_num = int(pline_m.group(1))
        elif anchor_m:
            explicit_num = int(anchor_m.group(1))

        if '{{gap}}' in raw:
            parts = raw.split('{{gap}}')
            a = clean_word(parts[0])
            b = clean_word(parts[1]) if len(parts) > 1 else ''
        else:
            # If no gap marker, try to detect a/b by whitespace grouping
            a = clean_word(raw)
            b = ''

        if not a and not b:
            continue

        line_num += 1
        if explicit_num is not None and explicit_num >= line_num:
            line_num = explicit_num

        if line_num not in lines_out:
            lines_out[line_num] = (a, b)

    return lines_out


def parse_hall_translation(text: str) -> dict[int, str]:
    start = text.find('*** START OF THE PROJECT GUTENBERG')
    end = text.find('*** END OF THE PROJECT GUTENBERG')
    if start != -1:
        text = text[start:end if end != -1 else len(text)]

    stanzas = re.split(r'\n{2,}', text)
    result: dict[int, str] = {}
    line_cursor = 1

    for stanza in stanzas:
        stanza = stanza.strip()
        if not stanza or len(stanza) < 10:
            continue
        if re.match(r'^[A-Z\s\.\-]+$', stanza) and len(stanza) < 80:
            continue
        if stanza.startswith('[') or stanza.startswith('_') or stanza.startswith('*'):
            continue
        n_lines = max(1, len(stanza.split('\n')))
        result[line_cursor] = ' '.join(stanza.split())
        line_cursor += n_lines * 2  # ~2 OE lines per Hall line

    return result


def find_translation(hall: dict[int, str], line_num: int) -> str:
    if line_num in hall:
        return hall[line_num]
    for n in range(line_num, max(0, line_num - 30), -1):
        if n in hall:
            return hall[n]
    return ""


def main() -> None:
    print("Fetching OE text from Wikisource…")
    ws_json = fetch(WIKISOURCE_API)
    ws_data = json.loads(ws_json)
    pages = ws_data["query"]["pages"]
    page = list(pages.values())[0]
    wikitext = page["revisions"][0]["slots"]["main"]["*"]
    print(f"  Wikitext length: {len(wikitext):,} chars")

    print("Parsing OE text…")
    oe_lines = parse_oe_wikitext(wikitext)
    print(f"  Parsed {len(oe_lines)} OE lines (max={max(oe_lines) if oe_lines else 0})")

    print("Fetching Hall translation…")
    try:
        hall_text = fetch(GUTENBERG_HALL)
        hall = parse_hall_translation(hall_text)
        print(f"  Parsed {len(hall)} Hall stanzas")
    except Exception as e:
        print(f"  Warning: {e}")
        hall = {}

    print("Building JSON…")
    sections = []
    for (num, title, line_start, line_end) in FITTS:
        lines = []
        for ln in range(line_start, line_end + 1):
            a, b = oe_lines.get(ln, ("", ""))
            translation = find_translation(hall, ln)
            lines.append({"num": ln, "a": a, "b": b, "translation": translation})
        sections.append({
            "id": f"fitt-{num.lower()}",
            "num": num,
            "title": title,
            "lineStart": line_start,
            "lineEnd": line_end,
            "lines": lines,
        })

    doc = {
        "title": "Beowulf",
        "date": "c. 700–1000 CE",
        "manuscript": "British Library, Cotton Vitellius A.xv",
        "textSource": "Harrison & Sharp (1883), via Wikisource (public domain)",
        "translationSource": "J. Lesslie Hall (1892), Project Gutenberg #16328 (public domain)",
        "sections": sections,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(s["lines"]) for s in sections)
    with_oe = sum(1 for s in sections for l in s["lines"] if l["a"] or l["b"])
    print(f"Wrote {OUT}  ({total} lines, {with_oe} with OE text)")


if __name__ == "__main__":
    main()
