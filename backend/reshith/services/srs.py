"""SM-2 Spaced Repetition Algorithm implementation."""

from dataclasses import dataclass
from datetime import datetime, timedelta


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
) -> SRSUpdate:
    """
    Calculate the next review state using the SM-2 algorithm.

    Args:
        quality: Response quality (0-5)
            0 - Complete blackout
            1 - Incorrect, but remembered upon seeing answer
            2 - Incorrect, but answer seemed easy to recall
            3 - Correct with serious difficulty
            4 - Correct with some hesitation
            5 - Perfect response
        easiness_factor: Current easiness factor (>= 1.3)
        interval_days: Current interval in days
        repetitions: Number of successful repetitions

    Returns:
        SRSUpdate with new state values
    """
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5")

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        if repetitions == 0:
            interval_days = 1
        elif repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(interval_days * easiness_factor)

        repetitions += 1

    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)

    next_review = datetime.now() + timedelta(days=interval_days)

    return SRSUpdate(
        easiness_factor=new_ef,
        interval_days=interval_days,
        repetitions=repetitions,
        next_review=next_review,
    )
