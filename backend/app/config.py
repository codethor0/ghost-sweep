"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the ghost-sweep API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ghost-sweep"
    environment: str = Field(default="development", pattern="^(development|staging|production)$")
    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5432/ghost_sweep",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    jwt_secret_key: str = Field(default="change-me-in-production-use-long-random-value")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    auth_rate_limit_per_minute: int = 20


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance.

    Returns:
        Settings: Parsed application settings.
    """
    return Settings()
