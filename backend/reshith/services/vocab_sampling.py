"""SRS-weighted vocabulary sampling for exercise generation.

For an authenticated user we bias the sample toward unmastered or due cards;
for anonymous users we fall back to a uniform shuffle. The sampler is
deliberately type-agnostic — callers pass in their pool of generator-specific
vocab dataclasses keyed by `id_fn` (typically the native-script lemma).
"""

import random
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from reshith.db import models
from reshith.exercises.vocab_id import vocab_id

T = TypeVar("T")


async def sample_vocab(
    session: AsyncSession | None,
    user_id: UUID | None,
    language: str,
    pool: list[T],
    *,
    id_fn: Callable[[T], str],
    k: int,
) -> list[T]:
    """Return ``k`` items drawn from ``pool`` weighted by SRS state.

    Weights (per the plan):
      - never reviewed: 3.0
      - due now: 2.0 + days_overdue * 0.1
      - low EF (< 2.0): +1.0 bonus
      - far-future (next_review > 14d away and EF >= 2.5): 0.3

    Anonymous users (``user_id`` is None) get a uniform random sample.
    """
    if not pool:
        return []
    if k <= 0:
        return []
    if k >= len(pool):
        out = list(pool)
        random.shuffle(out)
        return out

    if user_id is None or session is None:
        return random.sample(pool, k)

    # Bulk fetch SRS state for every pool item that has a corresponding card.
    card_ids = [vocab_id(language, id_fn(item)) for item in pool]
    srs_rows = (
        await session.execute(
            select(models.SRSState).where(
                models.SRSState.user_id == user_id,
                models.SRSState.card_id.in_(card_ids),
            )
        )
    ).scalars().all()
    srs_by_card = {s.card_id: s for s in srs_rows}

    now = datetime.now(UTC)
    weights: list[float] = []
    for item, cid in zip(pool, card_ids):
        s = srs_by_card.get(cid)
        if s is None:
            weights.append(3.0)
            continue
        # next_review may be naive (some test seeds) — normalise to UTC.
        nr = s.next_review if s.next_review.tzinfo else s.next_review.replace(tzinfo=UTC)
        delta_days = (nr - now).total_seconds() / 86400.0
        if delta_days <= 0:
            w = 2.0 + (-delta_days) * 0.1
        elif delta_days > 14 and s.easiness_factor >= 2.5:
            w = 0.3
        else:
            w = 1.0
        if s.easiness_factor < 2.0:
            w += 1.0
        weights.append(w)

    return _weighted_sample_without_replacement(pool, weights, k)


def _weighted_sample_without_replacement(
    items: list[T], weights: list[float], k: int,
) -> list[T]:
    """Efraimidis-Spirakis reservoir sampling for weighted draws."""
    keys: list[tuple[float, int]] = []
    for i, w in enumerate(weights):
        # Guard against zero/negative weights — clamp to a small positive.
        wi = max(w, 1e-6)
        u = random.random()
        key = u ** (1.0 / wi)
        keys.append((key, i))
    keys.sort(reverse=True)
    return [items[i] for _, i in keys[:k]]


async def sample_patterns(
    session: AsyncSession | None,
    user_id: UUID | None,
    language: str,
    exercise_type: str,
    available_patterns: list[str],
    *,
    k: int,
    lookback: int = 50,
) -> list[str]:
    """Bias pattern selection toward patterns the user gets wrong.

    For anonymous users or with no history, returns a uniform random
    selection. ``k`` may exceed ``len(available_patterns)`` — duplicates are
    permitted since exercises typically draw multiple from the same pattern.
    """
    if not available_patterns:
        return []
    if user_id is None or session is None:
        return [random.choice(available_patterns) for _ in range(k)]

    # Pull recent attempts for this (user, language, exercise_type).
    rows = (
        await session.execute(
            select(models.ExerciseAttempt.pattern, models.ExerciseAttempt.correct)
            .where(
                models.ExerciseAttempt.user_id == user_id,
                models.ExerciseAttempt.language == language,
                models.ExerciseAttempt.exercise_type == exercise_type,
            )
            .order_by(models.ExerciseAttempt.attempted_at.desc())
            .limit(lookback)
        )
    ).all()

    # Default weight per pattern = 1.0. For each recent attempt, reward
    # incorrect (+0.5) and penalise correct (-0.2), with a floor at 0.2.
    weights = {p: 1.0 for p in available_patterns}
    for pattern, correct in rows:
        if pattern not in weights:
            continue
        weights[pattern] += -0.2 if correct else 0.5
    for p in weights:
        weights[p] = max(0.2, weights[p])

    population = list(weights.keys())
    pop_weights = [weights[p] for p in population]
    return random.choices(population, weights=pop_weights, k=k)
