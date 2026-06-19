"""Tests for the sparse SRS config merge function (pure, no DB)."""

from reshith.services.srs import DEFAULTS, merge_config


def test_empty_user_and_deck_returns_defaults():
    result = merge_config({}, None)

    assert result == DEFAULTS


def test_user_overrides_defaults():
    result = merge_config({"easy_bonus": 1.5, "new_cards_per_day": 30}, None)

    assert result.easy_bonus == 1.5
    assert result.new_cards_per_day == 30
    # Untouched fields stay at default.
    assert result.minimum_ef == DEFAULTS.minimum_ef


def test_deck_overrides_user():
    user = {"easy_bonus": 1.5, "new_cards_per_day": 30}
    deck = {"easy_bonus": 2.0}

    result = merge_config(user, deck)

    assert result.easy_bonus == 2.0          # deck wins
    assert result.new_cards_per_day == 30    # user still applies
    assert result.minimum_ef == DEFAULTS.minimum_ef


def test_none_in_deck_means_inherit_not_override():
    user = {"easy_bonus": 1.5}
    deck = {"easy_bonus": None, "hard_multiplier": 1.4}

    result = merge_config(user, deck)

    assert result.easy_bonus == 1.5     # deck None → inherit user
    assert result.hard_multiplier == 1.4


def test_unknown_keys_are_ignored():
    # Forward-compatibility: extra keys (e.g. legacy fields, future ones not
    # yet wired into the dataclass) don't crash the merge.
    result = merge_config({"unknown": 42, "easy_bonus": 1.5}, None)
    assert result.easy_bonus == 1.5


def test_deck_can_override_with_zero_values():
    # Zero is a meaningful override (not the same as "unset").
    user = {"lapse_multiplier": 0.5}
    deck = {"lapse_multiplier": 0.0}

    result = merge_config(user, deck)

    # Zero is falsy but is not None, so the merge must take it.
    assert result.lapse_multiplier == 0.0
