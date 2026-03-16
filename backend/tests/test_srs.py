"""Tests for the SM-2 spaced repetition algorithm."""

from reshith.services.srs import calculate_sm2


def test_perfect_response_increases_interval():
    result = calculate_sm2(quality=5, easiness_factor=2.5, interval_days=1, repetitions=1)

    assert result.interval_days == 6
    assert result.repetitions == 2
    assert result.easiness_factor > 2.5


def test_failed_response_resets_repetitions():
    result = calculate_sm2(quality=2, easiness_factor=2.5, interval_days=10, repetitions=5)

    assert result.interval_days == 1
    assert result.repetitions == 0


def test_easiness_factor_minimum():
    result = calculate_sm2(quality=0, easiness_factor=1.3, interval_days=1, repetitions=0)

    assert result.easiness_factor >= 1.3


def test_first_review():
    result = calculate_sm2(quality=4, easiness_factor=2.5, interval_days=0, repetitions=0)

    assert result.interval_days == 1
    assert result.repetitions == 1


def test_second_review():
    result = calculate_sm2(quality=4, easiness_factor=2.5, interval_days=1, repetitions=1)

    assert result.interval_days == 6
    assert result.repetitions == 2
