"""Per-user, per-language primary deck management.

A "primary deck" is the auto-provisioned deck used by the self-paced lesson
flow: vocabulary cards from lesson JSON are seeded into it with deterministic
IDs so SRS state accumulates across sessions, lessons, and exercises.

Other (user-created) decks coexist; we only ever have one `is_primary=True`
deck per (owner_id, language) — enforced by partial unique index in the
migration.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.db import models
from reshith.exercises.vocab_id import vocab_id

# Display name used when the primary deck is auto-created.
_LANGUAGE_DISPLAY = {
    models.LanguageCode.BIBLICAL_HEBREW: "Biblical Hebrew",
    models.LanguageCode.LATIN: "Classical Latin",
    models.LanguageCode.ECCLESIASTICAL_LATIN: "Ecclesiastical Latin",
    models.LanguageCode.ANCIENT_GREEK: "Ancient Greek",
    models.LanguageCode.NT_GREEK: "NT Greek",
    models.LanguageCode.SANSKRIT: "Sanskrit",
    models.LanguageCode.PALI: "Pali",
    models.LanguageCode.BUDDHIST_HYBRID_SANSKRIT: "Buddhist Hybrid Sanskrit",
    models.LanguageCode.ARAMAIC: "Aramaic",
    models.LanguageCode.MIDRASHIC_HEBREW: "Midrashic Hebrew",
}


@dataclass
class VocabSeed:
    """Minimal shape required to seed a vocab card.

    Generators in this codebase use a few different dataclasses
    (`VocabularyItem`, `LatinWord`, `GreekWord`, `SanskritWord`); rather than
    couple the deck service to any of them, callers pass these flat seed
    objects.
    """
    lemma: str           # The native-script form used as the stable identifier.
    definition: str
    transliteration: str | None = None
    category: str | None = None
    lesson: int | None = None
    notes: str | None = None


async def get_or_create_primary_deck(
    session: AsyncSession,
    user_id: UUID,
    language: models.LanguageCode,
) -> models.Deck:
    """Return the primary deck for (user, language), creating one if absent."""
    result = await session.execute(
        select(models.Deck).where(
            models.Deck.owner_id == user_id,
            models.Deck.language == language,
            models.Deck.is_primary.is_(True),
        )
    )
    deck = result.scalar_one_or_none()
    if deck is not None:
        return deck

    display = _LANGUAGE_DISPLAY.get(language, language.value)
    deck = models.Deck(
        owner_id=user_id,
        language=language,
        name=f"{display} (auto)",
        description="Auto-provisioned lesson deck — tracks SRS state for lesson vocab.",
        is_primary=True,
    )
    session.add(deck)
    await session.flush()
    return deck


async def ensure_cards_for_vocab(
    session: AsyncSession,
    deck: models.Deck,
    vocab_items: list[VocabSeed],
) -> dict[UUID, models.Card]:
    """Idempotently insert cards for the given vocab into ``deck``.

    Card.id is set to ``vocab_id(language, lemma)`` so subsequent calls
    short-circuit via ON CONFLICT DO NOTHING and existing SRS state is
    preserved across re-seeds.
    """
    if not vocab_items:
        return {}

    language = deck.language.value if hasattr(deck.language, "value") else deck.language
    rows = []
    seen: set[UUID] = set()
    for v in vocab_items:
        cid = vocab_id(language, v.lemma)
        if cid in seen:
            continue
        seen.add(cid)
        rows.append({
            "id": cid,
            "deck_id": deck.id,
            "front": v.lemma,
            "back": v.definition,
            "transliteration": v.transliteration,
            "grammatical_info": v.category,
            "notes": v.notes,
            "source_reference": f"lesson{v.lesson:02d}" if v.lesson else None,
        })

    if not rows:
        return {}

    # On conflict, backfill any column the existing row left blank. This
    # matters because the by-lemma SUBMIT_REVIEW flow inserts a stub
    # card (definition="") before the user has visited the lesson page;
    # when set_current_lesson later calls us with the full lesson data,
    # we need to overwrite those blanks rather than silently keep the stub.
    stmt = pg_insert(models.Card).values(rows)
    excluded = stmt.excluded
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "back": _coalesce_if_blank(models.Card.back, excluded.back),
            "transliteration": _coalesce_if_blank(
                models.Card.transliteration, excluded.transliteration
            ),
            "grammatical_info": _coalesce_if_blank(
                models.Card.grammatical_info, excluded.grammatical_info
            ),
            "source_reference": _coalesce_if_blank(
                models.Card.source_reference, excluded.source_reference
            ),
            "notes": _coalesce_if_blank(models.Card.notes, excluded.notes),
        },
    )
    await session.execute(stmt)

    # Fetch the (now-present) rows so callers can map id → card.
    ids = [r["id"] for r in rows]
    fetched = await session.execute(select(models.Card).where(models.Card.id.in_(ids)))
    return {c.id: c for c in fetched.scalars().all()}


def _coalesce_if_blank(existing, new_value):
    """SQL expression: return ``new_value`` when ``existing`` is NULL or
    empty string, else keep ``existing``."""
    from sqlalchemy import case
    return case(
        ((existing.is_(None)) | (existing == ""), new_value),
        else_=existing,
    )
