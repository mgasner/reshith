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

    google_cloud_api_key: str = ""
    google_tts_voice: str = "he-IL-Wavenet-A"

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
