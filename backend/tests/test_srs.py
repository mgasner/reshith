"""Tests for the configurable SM-2 spaced repetition algorithm."""

from dataclasses import replace

from reshith.services.srs import DEFAULTS, calculate_sm2

# ── Defaults / SM-2 backbone ─────────────────────────────────────────────────


def test_perfect_response_grows_interval_via_easy_bonus():
    # rep 1 with EF=2.5 and default easy_bonus=1.3 → 1 * 2.5 * 1.3 = 3.25 → 3
    result = calculate_sm2(quality=5, easiness_factor=2.5, interval_days=1, repetitions=1)

    assert result.interval_days == 3
    assert result.repetitions == 2
    assert result.easiness_factor > 2.5


def test_failed_response_resets_to_lapse_minimum():
    result = calculate_sm2(quality=2, easiness_factor=2.5, interval_days=10, repetitions=5)

    # lapse_multiplier=0 by default → falls back to lapse_minimum_interval_days
    assert result.interval_days == DEFAULTS.lapse_minimum_interval_days
    assert result.repetitions == 0


def test_easiness_factor_floored_at_minimum_ef():
    result = calculate_sm2(quality=0, easiness_factor=1.3, interval_days=1, repetitions=0)

    assert result.easiness_factor >= DEFAULTS.minimum_ef


def test_first_review_uses_graduating_interval():
    # Good on a new card graduates with `graduating_interval_days`.
    result = calculate_sm2(quality=4, easiness_factor=2.5, interval_days=0, repetitions=0)

    assert result.interval_days == DEFAULTS.graduating_interval_days
    assert result.repetitions == 1


def test_first_review_easy_uses_easy_interval():
    result = calculate_sm2(quality=5, easiness_factor=2.5, interval_days=0, repetitions=0)

    assert result.interval_days == DEFAULTS.easy_interval_days


def test_second_review_uses_sm2_growth():
    result = calculate_sm2(quality=4, easiness_factor=2.5, interval_days=1, repetitions=1)

    # 1 * 2.5 = 2.5 → 2 with rounding
    assert result.interval_days == round(1 * 2.5)
    assert result.repetitions == 2


# ── Config-aware behavior ────────────────────────────────────────────────────


def test_easy_bonus_applied_on_quality_five():
    config = replace(DEFAULTS, easy_bonus=2.0)
    result = calculate_sm2(
        quality=5, easiness_factor=2.5, interval_days=10, repetitions=3, config=config
    )

    # 10 * 2.5 * 2.0 = 50
    assert result.interval_days == 50


def test_hard_multiplier_applied_on_quality_three():
    config = replace(DEFAULTS, hard_multiplier=1.5)
    result = calculate_sm2(
        quality=3, easiness_factor=2.5, interval_days=10, repetitions=3, config=config
    )

    # 10 * 1.5 = 15 (EF is ignored on Hard)
    assert result.interval_days == 15


def test_lapse_uses_multiplier_and_minimum():
    config = replace(DEFAULTS, lapse_multiplier=0.5, lapse_minimum_interval_days=3)

    # interval 20 → 10; floor still beats minimum (3)
    out_a = calculate_sm2(
        quality=1, easiness_factor=2.5, interval_days=20, repetitions=5, config=config
    )
    assert out_a.interval_days == 10

    # interval 4 → 2 — but lapse_minimum is 3 so clamp upward
    out_b = calculate_sm2(
        quality=1, easiness_factor=2.5, interval_days=4, repetitions=5, config=config
    )
    assert out_b.interval_days == 3


def test_interval_modifier_scales_review_intervals():
    config = replace(DEFAULTS, interval_modifier=0.5)
    result = calculate_sm2(
        quality=4, easiness_factor=2.5, interval_days=10, repetitions=3, config=config
    )

    # 10 * 2.5 = 25; modifier 0.5 → 12 or 13 depending on rounding.
    assert result.interval_days == round(25 * 0.5)


def test_maximum_interval_clamps_growth():
    config = replace(DEFAULTS, maximum_interval_days=30)
    result = calculate_sm2(
        quality=5, easiness_factor=3.0, interval_days=100, repetitions=4, config=config
    )

    assert result.interval_days == 30


def test_initial_ef_respected_via_minimum_ef():
    # Setting a high minimum forces the new EF to stay at or above it.
    config = replace(DEFAULTS, minimum_ef=2.7)
    result = calculate_sm2(
        quality=0, easiness_factor=2.5, interval_days=1, repetitions=0, config=config
    )

    assert result.easiness_factor >= 2.7
