"""Tests for the Fernet-based secrets crypto helpers.

These tests rely on swapping the cached settings so we can flip the
encryption key on/off without leaking state into the rest of the suite.
"""

import pytest
from cryptography.fernet import Fernet

from reshith.core import config
from reshith.services import crypto


@pytest.fixture(autouse=True)
def _reset_crypto_cache():
    """Each test gets a clean Fernet singleton + settings cache."""
    config.get_settings.cache_clear()
    crypto._fernet.cache_clear()
    yield
    config.get_settings.cache_clear()
    crypto._fernet.cache_clear()


def _set_key(monkeypatch, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv("SECRETS_ENCRYPTION_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRETS_ENCRYPTION_KEY", value)


def test_roundtrip_with_configured_key(monkeypatch):
    _set_key(monkeypatch, Fernet.generate_key().decode())

    token = crypto.encrypt("sk-test-1234567890")
    assert token != "sk-test-1234567890"
    assert crypto.decrypt(token) == "sk-test-1234567890"


def test_encrypt_without_key_raises(monkeypatch):
    _set_key(monkeypatch, "")

    assert crypto.is_configured() is False
    with pytest.raises(crypto.SecretsEncryptionNotConfiguredError):
        crypto.encrypt("anything")


def test_decrypt_handles_none_and_empty(monkeypatch):
    _set_key(monkeypatch, Fernet.generate_key().decode())

    assert crypto.decrypt(None) is None
    assert crypto.decrypt("") is None


def test_decrypt_invalid_token_returns_none(monkeypatch):
    _set_key(monkeypatch, Fernet.generate_key().decode())

    # A token encrypted under a different key cannot be decrypted; we return
    # None rather than raising so call sites can fall back gracefully.
    other_token = Fernet(Fernet.generate_key()).encrypt(b"hello").decode()
    assert crypto.decrypt(other_token) is None
