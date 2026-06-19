"""Lesson-progress book-keeping.

Centralises the read/write logic for `LessonProgress`, plus the mastery and
"ready to advance" calculations used by the GraphQL types.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.db import models
from reshith.exercises.vocab_id import vocab_id
from reshith.services import primary_deck, vocab_catalog

# Mastery threshold matches the plan's proposal: 80% of lesson vocab in a
# "well-known" state. "Mastered" = SM-2 repetitions >= 2 AND EF >= 2.3.
MASTERY_THRESHOLD = 0.8
MASTERY_REPETITIONS = 2
MASTERY_EF = 2.3


@dataclass
class ProgressInfo:
    language: models.LanguageCode
    current_lesson: int
    total_lessons: int
    vocab_total: int
    vocab_mastered: int
    due_count: int

    @property
    def mastery_percent(self) -> float:
        if self.vocab_total == 0:
            return 0.0
        return self.vocab_mastered / self.vocab_total

    @property
    def is_ready_to_advance(self) -> bool:
        return (
            self.current_lesson < self.total_lessons
            and self.mastery_percent >= MASTERY_THRESHOLD
        )


async def _get_progress_row(
    session: AsyncSession, user_id: UUID, language: models.LanguageCode,
) -> models.LessonProgress:
    result = await session.execute(
        select(models.LessonProgress).where(
            models.LessonProgress.user_id == user_id,
            models.LessonProgress.language == language,
        )
    )
    row = result.scalar_one_or_none()
    if row is not None:
        return row
    row = models.LessonProgress(user_id=user_id, language=language, current_lesson=1)
    session.add(row)
    await session.flush()
    return row


async def get_current_lesson(
    session: AsyncSession, user_id: UUID, language: models.LanguageCode,
) -> int:
    row = await _get_progress_row(session, user_id, language)
    return row.current_lesson


async def get_progress(
    session: AsyncSession, user_id: UUID, language: models.LanguageCode,
) -> ProgressInfo:
    """Read full progress info, auto-creating the row on first access."""
    row = await _get_progress_row(session, user_id, language)
    total = vocab_catalog.total_lessons(language)
    current = min(row.current_lesson, total) if total else row.current_lesson

    vocab_items = vocab_catalog.load_vocab(language, current)
    # Deduplicate by lemma so vocab_total reflects unique cards.
    unique_lemmas = {v.lemma for v in vocab_items}
    card_ids = [vocab_id(language.value, lemma) for lemma in unique_lemmas]

    if not card_ids:
        return ProgressInfo(
            language=language,
            current_lesson=current,
            total_lessons=total,
            vocab_total=0,
            vocab_mastered=0,
            due_count=0,
        )

    srs_q = select(models.SRSState).where(
        models.SRSState.user_id == user_id,
        models.SRSState.card_id.in_(card_ids),
    )
    srs_rows = (await session.execute(srs_q)).scalars().all()
    now = datetime.now(UTC)
    mastered = sum(
        1 for s in srs_rows
        if s.repetitions >= MASTERY_REPETITIONS and s.easiness_factor >= MASTERY_EF
    )

    def _to_aware(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    due = sum(
        1 for s in srs_rows
        if s.next_review is not None and _to_aware(s.next_review) <= now
    )
    # Unreviewed cards are also "due" (no SRSState row exists yet).
    reviewed_ids = {s.card_id for s in srs_rows}
    due += sum(1 for cid in card_ids if cid not in reviewed_ids)

    return ProgressInfo(
        language=language,
        current_lesson=current,
        total_lessons=total,
        vocab_total=len(unique_lemmas),
        vocab_mastered=mastered,
        due_count=due,
    )


async def set_current_lesson(
    session: AsyncSession,
    user_id: UUID,
    language: models.LanguageCode,
    lesson: int,
) -> ProgressInfo:
    """Set current_lesson directly (clamped to [1, total_lessons])."""
    row = await _get_progress_row(session, user_id, language)
    total = vocab_catalog.total_lessons(language) or lesson
    row.current_lesson = max(1, min(lesson, total))
    await session.flush()
    # Ensure cards exist for every lesson up to the new current lesson so SRS
    # state can begin to accumulate.
    deck = await primary_deck.get_or_create_primary_deck(session, user_id, language)
    items = vocab_catalog.load_vocab(language, row.current_lesson)
    await primary_deck.ensure_cards_for_vocab(session, deck, items)
    return await get_progress(session, user_id, language)


async def advance_lesson(
    session: AsyncSession, user_id: UUID, language: models.LanguageCode,
) -> ProgressInfo:
    """Increment current_lesson by 1 (capped to total)."""
    row = await _get_progress_row(session, user_id, language)
    return await set_current_lesson(
        session, user_id, language, row.current_lesson + 1,
    )


async def get_all_progress(
    session: AsyncSession, user_id: UUID,
) -> list[ProgressInfo]:
    """Return progress for every existing LessonProgress row + every language
    with lesson data the user has not yet started."""
    result = await session.execute(
        select(models.LessonProgress.language).where(
            models.LessonProgress.user_id == user_id,
        )
    )
    seen = {r[0] for r in result.all()}
    languages = list(seen)
    # Also include all languages that have lesson data so the navbar can show
    # "L1" for languages the user hasn't visited yet.
    for lang in vocab_catalog._LESSON_DIRS.keys():
        if lang not in seen and vocab_catalog.total_lessons(lang) > 0:
            languages.append(lang)
    out = []
    for lang in languages:
        out.append(await get_progress(session, user_id, lang))
    return out


# Avoid unused-import warning for func; kept for future aggregations.
_ = func
