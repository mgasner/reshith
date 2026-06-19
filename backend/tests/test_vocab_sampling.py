"""Test the weighted sampler's basic behaviour."""

import random

from reshith.services.vocab_sampling import _weighted_sample_without_replacement


def test_weighted_sample_returns_requested_count():
    random.seed(0)
    items = list(range(10))
    weights = [1.0] * 10
    out = _weighted_sample_without_replacement(items, weights, k=3)
    assert len(out) == 3
    assert len(set(out)) == 3  # no duplicates


def test_weighted_sample_biases_toward_heavy_weight():
    """With a 1000:1 weight ratio, the heavy item should appear in the
    first slot of nearly every sample."""
    items = ["heavy", "light"]
    weights = [1000.0, 0.001]
    chosen_heavy = 0
    for _ in range(100):
        out = _weighted_sample_without_replacement(items, weights, k=1)
        if out[0] == "heavy":
            chosen_heavy += 1
    assert chosen_heavy >= 95


def test_weighted_sample_empty_pool():
    assert _weighted_sample_without_replacement([], [], k=5) == []
