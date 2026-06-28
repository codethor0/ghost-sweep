"""Application configuration loaded from environment variables.

JWT secret policy:
- production and staging: JWT_SECRET_KEY is required and must be at least 32 characters
- development and test: JWT_SECRET_KEY is optional; a local-only default is applied when unset
"""

from functools import lru_cache
from typing import Any, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-not-for-production-use-min-32-chars"  # nosec B105


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

    jwt_secret_key: str | None = Field(default=None)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    auth_rate_limit_per_minute: int = 20

    @model_validator(mode="before")
    @classmethod
    def apply_development_jwt_default(cls, data: Any) -> Any:
        """Apply a local-only JWT default when non-production secrets are omitted."""
        if not isinstance(data, dict):
            return data

        environment = data.get("environment", "development")
        if environment == "development" and data.get("jwt_secret_key") is None:
            data["jwt_secret_key"] = DEVELOPMENT_JWT_SECRET
        return data

    @model_validator(mode="after")
    def validate_production_jwt_secret(self) -> Self:
        """Require explicit JWT secrets in production and staging."""
        if self.environment in {"production", "staging"} and (
            self.jwt_secret_key is None or len(self.jwt_secret_key.strip()) < 32
        ):
            raise ValueError(
                f"{self.environment.capitalize()} deployments must set JWT_SECRET_KEY to a "
                "secret of at least 32 characters."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance.

    Returns:
        Settings: Parsed application settings.
    """
    return Settings()
