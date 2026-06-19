"""SM-2 Spaced Repetition Algorithm implementation with Anki-style configuration."""

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime, timedelta

# ── Configuration ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SRSConfig:
    """Anki-style spaced repetition configuration.

    Note: classic Anki "learning steps" (sub-day intervals before a card
    graduates) and the "leech" workflow are intentionally not modelled here —
    ``calculate_sm2`` is a day-granularity algorithm and the schema would lie
    about what it does if those knobs were exposed but unimplemented.
    """

    # Initial state
    initial_ef: float = 2.5
    minimum_ef: float = 1.3
    # First-graduation intervals
    graduating_interval_days: int = 1
    easy_interval_days: int = 4
    # Review intervals
    hard_multiplier: float = 1.2
    easy_bonus: float = 1.3
    interval_modifier: float = 1.0  # global "speed" knob
    maximum_interval_days: int = 36500
    # Lapses
    lapse_multiplier: float = 0.0  # interval *= lapse_multiplier on fail (0 = reset)
    lapse_minimum_interval_days: int = 1
    # Daily caps
    new_cards_per_day: int = 20
    reviews_per_day: int = 200


DEFAULTS = SRSConfig()


# Field names that participate in configuration / merging.
CONFIG_FIELD_NAMES: tuple[str, ...] = tuple(f.name for f in fields(SRSConfig))


def merge_config(user: dict, deck: dict | None) -> SRSConfig:
    """Sparse merge: deck (non-None) > user (non-None) > DEFAULTS.

    Both ``user`` and ``deck`` are plain dicts whose keys are a subset of
    ``CONFIG_FIELD_NAMES``. Missing or ``None``-valued keys fall through to
    the next layer.
    """
    merged: dict = asdict(DEFAULTS)
    for name in CONFIG_FIELD_NAMES:
        if user is not None:
            value = user.get(name)
            if value is not None:
                merged[name] = value
        if deck is not None:
            value = deck.get(name)
            if value is not None:
                merged[name] = value
    return SRSConfig(**merged)


# ── Algorithm ────────────────────────────────────────────────────────────────


@dataclass
class SRSUpdate:
    easiness_factor: float
    interval_days: int
    repetitions: int
    next_review: datetime


def calculate_sm2(
    quality: int,
    easiness_factor: float,
    interval_days: int,
    repetitions: int,
    config: SRSConfig = DEFAULTS,
) -> SRSUpdate:
    """Calculate the next review state using a configurable SM-2 variant.

    Args:
        quality: Response quality (0-5)
            0 - Complete blackout
            1 - Incorrect, but remembered upon seeing answer
            2 - Incorrect, but answer seemed easy to recall
            3 - Correct with serious difficulty (Hard)
            4 - Correct with some hesitation (Good)
            5 - Perfect response (Easy)
        easiness_factor: Current easiness factor.
        interval_days: Current interval in days.
        repetitions: Number of successful repetitions.
        config: Active :class:`SRSConfig`. Defaults to module-level ``DEFAULTS``.

    Returns:
        :class:`SRSUpdate` with new state values.
    """
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5")

    if quality < 3:
        # Lapse
        repetitions = 0
        if config.lapse_multiplier <= 0:
            new_interval = config.lapse_minimum_interval_days
        else:
            new_interval = max(
                round(interval_days * config.lapse_multiplier),
                config.lapse_minimum_interval_days,
            )
        interval_days = new_interval
    else:
        if repetitions == 0:
            # Graduating from "new". Easy graduates straight to the longer
            # interval; Hard/Good graduate to the standard graduating interval.
            interval_days = (
                config.easy_interval_days
                if quality == 5
                else config.graduating_interval_days
            )
        else:
            # Standard SM-2 growth, with Anki-style per-quality modifiers.
            if quality == 3:
                base = interval_days * config.hard_multiplier
            elif quality == 5:
                base = interval_days * easiness_factor * config.easy_bonus
            else:
                base = interval_days * easiness_factor
            interval_days = round(base)

        interval_days = max(1, round(interval_days * config.interval_modifier))
        interval_days = min(interval_days, config.maximum_interval_days)
        repetitions += 1

    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(config.minimum_ef, new_ef)

    next_review = datetime.now(UTC) + timedelta(days=interval_days)

    return SRSUpdate(
        easiness_factor=new_ef,
        interval_days=interval_days,
        repetitions=repetitions,
        next_review=next_review,
    )


__all__ = [
    "SRSConfig",
    "SRSUpdate",
    "DEFAULTS",
    "CONFIG_FIELD_NAMES",
    "merge_config",
    "calculate_sm2",
]
