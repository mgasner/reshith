"""
Rashi enrichment pipeline — main entry point.

Usage:
  uv run python -m scripts.rashi_pipeline.run --all
  uv run python -m scripts.rashi_pipeline.run --book gen exo
  uv run python -m scripts.rashi_pipeline.run --book gen --dry-run
  uv run python -m scripts.rashi_pipeline.run --all --resume

Output written to: data/rashi_enriched/{book}/ch{N}.json
Each chapter file:
{
  "meta": { "book": "gen", "chapter": 1, "verse_count": 24, "processed_at": "..." },
  "verses": {
    "1": <EnrichedVerse.to_dict()>,
    ...
  }
}

The pipeline:
  1. Load raw Rashi JSON (HTML strings)
  2. Tokenize each comment (strip HTML, split words)
  3. Identify language per token (Hebrew/Aramaic/Old French/Abbreviation)
  4. Batch Hebrew+Aramaic tokens → Dicta API for morphological analysis
  5. Look up lemmas in Sefaria (BDB/Jastrow) and custom lexicon
  6. Assemble Token objects with uncertainty flags
  7. Write per-chapter JSON files
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .abbreviations import is_abbreviation, lookup_abbreviation
from .custom_lexicon import lookup_custom
from .dicta_client import DictaClient
from .language_id import LanguageIdentifier
from .models import DictionaryEntry, Language, Morphology, Token, UncertaintyReason
from .morph_parser import parse_morph_code
from .sefaria_lexicon import SefariaLexicon
from .tokenizer import is_hebrew_word, strip_vowels, tokenize_comment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
RASHI_SOURCE_DIR = REPO_ROOT / "frontend" / "public" / "data" / "hebrew" / "rashi"
OUTPUT_DIR = REPO_ROOT / "data" / "rashi_enriched"
CACHE_DIR = REPO_ROOT / "data" / ".pipeline_cache"

ALL_BOOKS = sorted(p.stem for p in RASHI_SOURCE_DIR.glob("*.json"))


# ---------------------------------------------------------------------------
# Per-token assembly
# ---------------------------------------------------------------------------

def _build_token(
    surface: str,
    is_bold: bool,
    language: Language,
    dicta_result: object | None,  # DictaToken | None
    dictionary: DictionaryEntry | None,
) -> Token:
    from .dicta_client import DictaToken

    normalized = strip_vowels(surface)
    token = Token(
        surface=surface,
        normalized=normalized,
        language=language,
        is_biblical_quote=is_bold,
    )

    # Abbreviation handling
    if language == Language.ABBREVIATION:
        token.uncertain = True
        token.uncertainty_reasons.append(UncertaintyReason.ABBREVIATION)
        expansion = lookup_abbreviation(surface)
        if expansion:
            token.abbreviation_expansion = f"{expansion[0]} — {expansion[1]}"
        else:
            token.uncertainty_reasons.append(UncertaintyReason.UNKNOWN_EXPANSION)
        token.dictionary = dictionary
        return token

    # Old French handling
    if language == Language.OLD_FRENCH:
        token.uncertain = True
        token.uncertainty_reasons.append(UncertaintyReason.OLD_FRENCH)
        # Check custom laaz lexicon
        custom = lookup_custom(surface)
        if custom:
            token.dictionary = DictionaryEntry(
                source=custom["source"],
                headword=custom["headword"],
                gloss=custom["gloss"],
                definition=custom.get("definition"),
            )
        else:
            token.uncertainty_reasons.append(UncertaintyReason.NO_DICTIONARY)
        return token

    # Aramaic: flag but still process morphology
    if language == Language.ARAMAIC:
        token.uncertainty_reasons.append(UncertaintyReason.ARAMAIC)
        token.uncertain = True

    # Morphological analysis from Dicta
    if isinstance(dicta_result, DictaToken):
        dt = dicta_result
        if dt.lemma:
            token.lemma = dt.lemma
        if dt.morph_code:
            morph = parse_morph_code(dt.morph_code)
            token.morphology = morph
        token.confidence = dt.confidence

        if dt.is_uncertain:
            token.uncertain = True
            token.uncertainty_reasons.append(UncertaintyReason.LOW_CONFIDENCE)
        if dt.has_multiple_analyses:
            token.uncertain = True
            token.uncertainty_reasons.append(UncertaintyReason.MULTIPLE_ANALYSES)
        if not dt.options:
            token.uncertain = True
            token.uncertainty_reasons.append(UncertaintyReason.UNRECOGNIZED)

        alts = dt.top_alternatives()
        if alts:
            token.alternatives = alts
    elif language not in (Language.PUNCTUATION, Language.UNKNOWN):
        token.uncertain = True
        token.uncertainty_reasons.append(UncertaintyReason.UNRECOGNIZED)

    # Dictionary entry
    if dictionary:
        token.dictionary = dictionary
    elif language not in (Language.PUNCTUATION, Language.UNKNOWN):
        if not any(r == UncertaintyReason.NO_DICTIONARY for r in token.uncertainty_reasons):
            token.uncertainty_reasons.append(UncertaintyReason.NO_DICTIONARY)

    return token


# ---------------------------------------------------------------------------
# Per-verse processing
# ---------------------------------------------------------------------------

async def process_verse(
    chapter: int,
    verse: int,
    html: str,
    dicta: DictaClient,
    sefaria: SefariaLexicon,
    lang_id: LanguageIdentifier,
) -> dict:
    from .models import EnrichedVerse
    from .dicta_client import DictaToken

    lang_id.reset()

    # Step 1: tokenize
    raw_tokens = tokenize_comment(html)  # [(surface, is_bold), ...]

    # Step 2: language identification
    tagged: list[tuple[str, bool, Language]] = []
    for surface, is_bold in raw_tokens:
        lang = lang_id.identify(surface)
        tagged.append((surface, is_bold, lang))

    # Step 3: collect tokens that need Dicta analysis
    # Only analyze Hebrew and Aramaic (not punctuation, Old French, abbreviations)
    to_analyze: list[tuple[int, str]] = []  # (index, surface)
    for i, (surface, _, lang) in enumerate(tagged):
        if lang in (Language.HEBREW, Language.ARAMAIC) and is_hebrew_word(surface):
            to_analyze.append((i, surface))

    # Step 4: Dicta analysis — cache-aware, only fetches cache misses
    dicta_results: dict[int, object] = {}
    if to_analyze:
        indices = [idx for idx, _ in to_analyze]
        surfaces = [s for _, s in to_analyze]
        try:
            results = await dicta.analyze_tokens(surfaces)
            for idx, result in zip(indices, results):
                dicta_results[idx] = result
        except Exception as e:
            logger.warning(f"Dicta analysis failed for ch{chapter}:v{verse}: {e}")

    # Step 5: collect unique lemmas for Sefaria lookup
    unique_lemmas: set[str] = set()
    for dicta_result in dicta_results.values():
        from .dicta_client import DictaToken as DT
        if isinstance(dicta_result, DT) and dicta_result.lemma:
            unique_lemmas.add(strip_vowels(dicta_result.lemma))

    # Sefaria lookups — run concurrently (each is independent; Sefaria has its own
    # internal throttle + disk cache, so parallel coroutines serialise via _throttle)
    lemma_entries = await asyncio.gather(
        *[sefaria.lookup(lemma) for lemma in unique_lemmas],
        return_exceptions=True,
    )
    lemmas: dict[str, DictionaryEntry | None] = {}
    for lemma, entry in zip(unique_lemmas, lemma_entries):
        lemmas[lemma] = entry if not isinstance(entry, BaseException) else None

    # Step 6: assemble Token objects
    tokens: list[Token] = []
    for i, (surface, is_bold, lang) in enumerate(tagged):
        dicta_result = dicta_results.get(i)
        # Get dictionary entry via lemma
        dictionary: DictionaryEntry | None = None
        from .dicta_client import DictaToken as DT
        if isinstance(dicta_result, DT) and dicta_result.lemma:
            dictionary = lemmas.get(strip_vowels(dicta_result.lemma))
        # Check custom lexicon as fallback
        if dictionary is None:
            custom = lookup_custom(surface)
            if custom:
                dictionary = DictionaryEntry(
                    source=custom["source"],
                    headword=custom["headword"],
                    gloss=custom["gloss"],
                    definition=custom.get("definition"),
                )
        token = _build_token(surface, is_bold, lang, dicta_result, dictionary)
        tokens.append(token)

    verse_obj = EnrichedVerse(chapter=chapter, verse=verse, tokens=tokens)
    return verse_obj.to_dict()


# ---------------------------------------------------------------------------
# Per-book processing
# ---------------------------------------------------------------------------

async def process_book(
    book: str,
    dicta: DictaClient,
    sefaria: SefariaLexicon,
    dry_run: bool = False,
    resume: bool = False,
) -> None:
    source_path = RASHI_SOURCE_DIR / f"{book}.json"
    if not source_path.exists():
        logger.error(f"Source not found: {source_path}")
        return

    data = json.loads(source_path.read_text(encoding="utf-8"))
    book_out_dir = OUTPUT_DIR / book
    if not dry_run:
        book_out_dir.mkdir(parents=True, exist_ok=True)

    lang_id = LanguageIdentifier()
    total_chapters = len(data)

    for ch_idx, (ch_key, verses) in enumerate(data.items(), 1):
        chapter = int(ch_key)
        out_path = book_out_dir / f"ch{chapter}.json"

        if resume and out_path.exists():
            logger.info(f"  [{book}] ch{chapter} already done, skipping")
            continue

        logger.info(f"  [{book}] chapter {chapter}/{total_chapters} ({len(verses)} verses)")

        verse_results: dict[str, dict] = {}
        for vs_key, html in verses.items():
            verse = int(vs_key)
            try:
                result = await process_verse(chapter, verse, html, dicta, sefaria, lang_id)
                verse_results[vs_key] = result
            except Exception as e:
                logger.error(f"    Error at {book} {chapter}:{verse}: {e}", exc_info=True)
                verse_results[vs_key] = {"error": str(e), "tokens": []}

        chapter_doc = {
            "meta": {
                "book": book,
                "chapter": chapter,
                "verse_count": len(verses),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
            "verses": verse_results,
        }

        if dry_run:
            token_count = sum(len(v.get("tokens", [])) for v in verse_results.values())
            uncertain_count = sum(
                sum(1 for t in v.get("tokens", []) if t.get("uncertain"))
                for v in verse_results.values()
            )
            logger.info(
                f"    [dry-run] ch{chapter}: {token_count} tokens, "
                f"{uncertain_count} uncertain"
            )
        else:
            out_path.write_text(json.dumps(chapter_doc, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"    wrote {out_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> None:
    if args.all:
        books = ALL_BOOKS
    else:
        books = args.book or []
        invalid = [b for b in books if b not in ALL_BOOKS]
        if invalid:
            logger.error(f"Unknown books: {invalid}. Available: {ALL_BOOKS}")
            sys.exit(1)

    if not books:
        logger.error("Specify --all or --book <book> [book ...]")
        sys.exit(1)

    logger.info(f"Processing {len(books)} book(s): {', '.join(books)}")
    logger.info(f"Output: {OUTPUT_DIR}")
    if args.dry_run:
        logger.info("DRY RUN — no files will be written")
    if args.resume:
        logger.info("RESUME MODE — skipping already-processed chapters")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    async with DictaClient(cache_dir=CACHE_DIR, requests_per_second=1.0) as dicta:
        async with SefariaLexicon(CACHE_DIR, requests_per_second=2.0) as sefaria:
            for book in books:
                logger.info(f"=== {book.upper()} ===")
                await process_book(
                    book=book,
                    dicta=dicta,
                    sefaria=sefaria,
                    dry_run=args.dry_run,
                    resume=args.resume,
                )

    logger.info("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rashi morphological enrichment pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Process all books")
    group.add_argument("--book", nargs="+", metavar="BOOK", help="Process specific book(s) e.g. gen exo")
    parser.add_argument("--dry-run", action="store_true", help="Analyze but don't write output")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed chapters")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.output_dir != OUTPUT_DIR:
        OUTPUT_DIR = args.output_dir  # type: ignore[assignment]

    asyncio.run(main(args))
