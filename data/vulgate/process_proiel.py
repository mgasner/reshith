"""
Process the PROIEL Latin NT treebank XML into a TSV file for the Reshith app.

Input:  latin-nt.xml  (PROIEL treebank, ~22 MB)
Output: nt_tokens.tsv

Columns:
  ref         – e.g. MATT.1.1#01
  book        – e.g. MATT
  chapter     – integer
  verse       – integer
  token       – per-verse token number, starting at 1
  form        – surface Latin word
  lemma       – dictionary headword
  pos         – 2-char PROIEL POS code  (e.g. Nb, V-, Ne …)
  morphology  – 9-10 char morphology string
  relation    – dependency relation (sub, obj, pred, atr …)
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

XML_PATH = Path(__file__).parent / "latin-nt.xml"
TSV_PATH = Path(__file__).parent / "nt_tokens.tsv"

HEADER = ["ref", "book", "chapter", "verse", "token",
          "form", "lemma", "pos", "morphology", "relation"]


def parse_citation(citation_part: str):
    """'MATT 1.1' → ('MATT', 1, 1).  Returns None on parse failure."""
    try:
        book, chap_verse = citation_part.split(" ", 1)
        chapter_str, verse_str = chap_verse.split(".", 1)
        return book, int(chapter_str), int(verse_str)
    except (ValueError, AttributeError):
        return None


def make_ref(book: str, chapter: int, verse: int, token_num: int) -> str:
    return f"{book}.{chapter}.{verse}#{token_num:02d}"


def main():
    print(f"Parsing {XML_PATH} …")
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    source = root.find("source")
    if source is None:
        raise RuntimeError("No <source> element found in XML")

    rows = []

    # Track per-verse token counters: (book, chapter, verse) → next token num
    verse_token_count: dict[tuple, int] = {}

    for div in source.findall("div"):
        for sentence in div.findall("sentence"):
            for token in sentence.findall("token"):
                # Skip empty tokens (null elements inserted for ellipsis resolution)
                if token.get("empty-token-sort") is not None:
                    continue
                form = token.get("form", "")
                if not form:
                    continue

                citation_part = token.get("citation-part", "")
                parsed = parse_citation(citation_part)
                if parsed is None:
                    # Silently skip tokens whose citation can't be parsed
                    continue
                book, chapter, verse = parsed

                key = (book, chapter, verse)
                verse_token_count[key] = verse_token_count.get(key, 0) + 1
                token_num = verse_token_count[key]

                rows.append({
                    "ref": make_ref(book, chapter, verse, token_num),
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "token": token_num,
                    "form": form,
                    "lemma": token.get("lemma", ""),
                    "pos": token.get("part-of-speech", ""),
                    "morphology": token.get("morphology", ""),
                    "relation": token.get("relation", ""),
                })

    print(f"Writing {len(rows):,} tokens to {TSV_PATH} …")
    with open(TSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print("Done.")


if __name__ == "__main__":
    main()
