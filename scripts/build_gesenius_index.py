#!/usr/bin/env python3
"""Build the Gesenius Hebrew Grammar search index with OpenAI embeddings.

Usage (from repo root):
    OPENAI_API_KEY=sk-... uv run --directory backend python scripts/build_gesenius_index.py

Or with a backend/.env file:
    uv run --directory backend python scripts/build_gesenius_index.py
"""

import json
import os
import re
import sys
import time
from pathlib import Path

# Load .env from backend directory
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / "backend" / ".env")
except ImportError:
    pass

import openai

DATA_DIR = Path(__file__).parent.parent / "data" / "references"
RAW_TEXT = DATA_DIR / "gesenius_hebrew_grammar.txt"
INDEX_FILE = DATA_DIR / "gesenius_index.jsonl"

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_CHUNK_CHARS = 3000
# Only embed first N chars of each chunk to keep token usage reasonable
EMBED_CHARS = 1000


def normalize(text: str) -> str:
    """Normalize OCR text: collapse extra whitespace."""
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_sections(raw: str) -> list[dict]:
    """Parse the text into §-delimited sections, skipping the table of contents."""
    # The actual content begins at the second occurrence of §1 (after the ToC)
    content_start = raw.find("§  1.     The  Semitic  Languages")
    if content_start == -1:
        content_start = 0

    # Stop before the indexes at the back (they start with large § back-references)
    # Heuristic: find "INDEX OF SUBJECTS" or similar
    for end_marker in ["INDEX  OF  SUBJECTS", "INDEX OF SUBJECTS", "GENERAL INDEX"]:
        idx = raw.find(end_marker, content_start)
        if idx != -1:
            content_end = idx
            break
    else:
        content_end = len(raw)

    content = raw[content_start:content_end]

    # Match lines that start a new top-level section: §  N.  or §  Na.
    section_re = re.compile(r"^(§\s+\d+[a-z]?\.\s+.+)$", re.MULTILINE)
    matches = list(section_re.finditer(content))

    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        raw_chunk = content[start:end]
        first_newline = raw_chunk.find("\n")
        raw_title = raw_chunk[:first_newline].strip() if first_newline > 0 else raw_chunk[:100]

        title = normalize(raw_title)
        # Extract section number for the label
        sec_match = re.match(r"§\s+(\d+[a-z]?)\.", raw_title)
        sec_num = sec_match.group(1) if sec_match else str(i + 1)

        body = normalize(raw_chunk)
        if len(body) > MAX_CHUNK_CHARS:
            body = body[:MAX_CHUNK_CHARS] + " [...]"

        sections.append({"section": f"§{sec_num}", "title": title, "text": body})

    return sections


def embed_batch(client: openai.OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = openai.OpenAI(api_key=api_key)

    print(f"Reading {RAW_TEXT} ...")
    raw = RAW_TEXT.read_text(encoding="utf-8", errors="replace")

    print("Parsing sections ...")
    sections = parse_sections(raw)
    print(f"Found {len(sections)} sections")

    # If index already exists, skip sections we already have
    existing: dict[str, list[float]] = {}
    if INDEX_FILE.exists():
        with INDEX_FILE.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    if "embedding" in rec:
                        existing[rec["section"]] = rec["embedding"]
        print(f"  {len(existing)} sections already indexed, skipping those")

    to_embed = [s for s in sections if s["section"] not in existing]
    print(f"Embedding {len(to_embed)} sections with {EMBEDDING_MODEL} ...")

    batch_size = 50
    new_embeddings: dict[str, list[float]] = {}
    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i : i + batch_size]
        texts = [s["text"][:EMBED_CHARS] for s in batch]
        embeddings = embed_batch(client, texts)
        for sec, emb in zip(batch, embeddings):
            new_embeddings[sec["section"]] = emb
        print(f"  {min(i + batch_size, len(to_embed))}/{len(to_embed)}")
        if i + batch_size < len(to_embed):
            time.sleep(0.3)

    all_embeddings = {**existing, **new_embeddings}

    print(f"Writing index to {INDEX_FILE} ...")
    with INDEX_FILE.open("w", encoding="utf-8") as f:
        for section in sections:
            emb = all_embeddings.get(section["section"])
            record = {**section}
            if emb:
                record["embedding"] = emb
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Done. {len(sections)} sections written ({len(all_embeddings)} with embeddings).")


if __name__ == "__main__":
    main()
