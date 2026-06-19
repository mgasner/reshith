"""Symmetric encryption for user-supplied secrets (API keys).

Wraps :class:`cryptography.fernet.Fernet` with a process-wide singleton keyed
off ``settings.secrets_encryption_key``. The DB only ever stores ciphertext;
plaintext lives only on the wire (HTTPS) and in memory during a request.

If ``secrets_encryption_key`` is not configured, :func:`encrypt` raises so we
never silently persist plaintext secrets. :func:`decrypt` returns ``None`` on
empty input to make call sites concise.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from reshith.core.config import get_settings


class SecretsEncryptionNotConfigured(RuntimeError):
    """Raised when SECRETS_ENCRYPTION_KEY is not set but encryption is required."""


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = get_settings().secrets_encryption_key
    if not key:
        raise SecretsEncryptionNotConfigured(
            "SECRETS_ENCRYPTION_KEY is not configured. Generate one with "
            "`python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'` and set it in the backend "
            ".env before storing user-supplied API keys."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def is_configured() -> bool:
    """Whether the encryption key is available — for guarding UI surfaces."""
    return bool(get_settings().secrets_encryption_key)


def encrypt(plaintext: str) -> str:
    """Return a URL-safe base64 Fernet token for ``plaintext``."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str | None) -> str | None:
    """Decrypt a Fernet token. Returns ``None`` for empty/None input.

    Returns ``None`` (rather than raising) on InvalidToken — typically caused
    by the key being rotated without re-encrypting stored ciphertexts — so
    that LLM resolvers degrade to the env-var fallback instead of failing
    every request.
    """
    if not token:
        return None
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        return None
