"""Test the deterministic vocab_id helper."""

from reshith.exercises.vocab_id import vocab_id


def test_vocab_id_is_deterministic():
    a = vocab_id("hbo", "נַעַר")
    b = vocab_id("hbo", "נַעַר")
    assert a == b


def test_vocab_id_differs_by_language():
    assert vocab_id("hbo", "test") != vocab_id("lat", "test")


def test_vocab_id_differs_by_lemma():
    assert vocab_id("hbo", "a") != vocab_id("hbo", "b")
