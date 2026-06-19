"""Persist exercise attempts and roll up to SRS state.

Called from every `grade_*` mutation so that:
  1. The pattern/vocab sampler can bias future exercises away from mastered
     items and toward weak patterns (`ExerciseAttempt` rows).
  2. Grading an exercise correctly nudges the corresponding lesson card's
     SM-2 state forward (without requiring the user to also flip the
     flashcard).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.db import models
from reshith.exercises.vocab_id import vocab_id
from reshith.services import primary_deck, srs


def quality_from_grade(correct: bool, score: float | None) -> int:
    """Map exercise grading outcome to an SM-2 quality (1-5).

    Conservative per the plan: never apply ``5`` (reserved for the explicit
    "Easy" flashcard button).
    """
    if not correct:
        return 2
    if score is None:
        return 4
    if score >= 0.7:
        return 4
    return 3


async def record_attempt(
    session: AsyncSession,
    user_id: UUID | None,
    *,
    language: models.LanguageCode,
    exercise_type: str,
    correct: bool,
    pattern: str | None = None,
    vocab_lemma: str | None = None,
    score: float | None = None,
) -> None:
    """Insert an ExerciseAttempt row and update SRS for the lesson card.

    No-op for anonymous users (``user_id is None``).
    """
    if user_id is None:
        return

    cid = (
        vocab_id(language.value, vocab_lemma) if vocab_lemma else None
    )
    session.add(
        models.ExerciseAttempt(
            user_id=user_id,
            language=language,
            exercise_type=exercise_type,
            pattern=pattern,
            vocab_id=cid,
            correct=correct,
            score=score,
        )
    )

    # If we have a lemma, also nudge its SRS state — but only if a card
    # already exists in the primary deck (avoid auto-creating cards for
    # generator-only vocab the user has not seen as a flashcard yet).
    if cid is None:
        return

    card_present = (
        await session.execute(
            select(models.Card.id).where(models.Card.id == cid)
        )
    ).scalar_one_or_none()
    if card_present is None:
        # Lazily provision the card so SRS state has something to attach to.
        deck = await primary_deck.get_or_create_primary_deck(
            session, user_id, language,
        )
        await primary_deck.ensure_cards_for_vocab(
            session,
            deck,
            [primary_deck.VocabSeed(lemma=vocab_lemma, definition="")],
        )

    quality = quality_from_grade(correct, score)
    existing = (
        await session.execute(
            select(models.SRSState).where(
                models.SRSState.card_id == cid,
                models.SRSState.user_id == user_id,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        update = srs.calculate_sm2(
            quality=quality,
            easiness_factor=existing.easiness_factor,
            interval_days=existing.interval_days,
            repetitions=existing.repetitions,
        )
        existing.easiness_factor = update.easiness_factor
        existing.interval_days = update.interval_days
        existing.repetitions = update.repetitions
        existing.next_review = update.next_review
    else:
        update = srs.calculate_sm2(
            quality=quality,
            easiness_factor=2.5,
            interval_days=0,
            repetitions=0,
        )
        session.add(
            models.SRSState(
                card_id=cid,
                user_id=user_id,
                easiness_factor=update.easiness_factor,
                interval_days=update.interval_days,
                repetitions=update.repetitions,
                next_review=update.next_review,
            )
        )
