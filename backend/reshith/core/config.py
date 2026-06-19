from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Reshith"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://localhost:5432/reshith"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    # Default LLM provider used when a user has not selected one explicitly.
    # Must be "openai" or "anthropic".
    default_llm_provider: str = "openai"

    # Fernet key (base64-encoded 32 bytes) used to encrypt user-supplied API
    # keys at rest. Generate with: ``python -c "from cryptography.fernet import
    # Fernet; print(Fernet.generate_key().decode())"``. When empty the API-key
    # storage endpoints reject writes so we never persist plaintext secrets.
    secrets_encryption_key: str = ""

    google_cloud_api_key: str = ""
    google_tts_voice: str = "he-IL-Wavenet-A"

    # HuggingFace token — required to download gated models (e.g. indic-parler-tts).
    # Set via HF_TOKEN in .env or environment.
    hf_token: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week


@lru_cache
def get_settings() -> Settings:
    return Settings()
