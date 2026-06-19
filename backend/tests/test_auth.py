"""Tests for password hashing and JWT helpers."""

from uuid import uuid4

from reshith.services.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("hunter2hunter2")
    assert hashed != "hunter2hunter2"
    assert verify_password("hunter2hunter2", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_password_hash_is_salted():
    a = hash_password("same-password")
    b = hash_password("same-password")
    # bcrypt uses a per-call salt so two hashes of the same plaintext differ.
    assert a != b
    assert verify_password("same-password", a)
    assert verify_password("same-password", b)


def test_token_roundtrip():
    user_id = uuid4()
    token = create_access_token(user_id)
    assert decode_token(token) == user_id


def test_token_invalid_returns_none():
    assert decode_token("not-a-real-token") is None
