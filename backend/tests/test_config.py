"""Configuration validation tests."""

import pytest
from pydantic import ValidationError

from app.config import DEVELOPMENT_JWT_SECRET, Settings


def test_production_settings_without_jwt_secret_raises_validation_error() -> None:
    """Production must reject missing JWT secrets."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(environment="production", jwt_secret_key=None)


def test_production_settings_with_short_jwt_secret_raises_validation_error() -> None:
    """Production must reject JWT secrets shorter than 32 characters."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(environment="production", jwt_secret_key="too-short")


def test_production_settings_with_valid_jwt_secret_succeeds() -> None:
    """Production accepts an explicit JWT secret of sufficient length."""
    settings = Settings(
        environment="production",
        jwt_secret_key="production-secret-with-sufficient-length",
    )
    assert settings.jwt_secret_key == "production-secret-with-sufficient-length"


def test_development_settings_without_jwt_secret_uses_dev_default() -> None:
    """Development may run without JWT_SECRET_KEY using a local-only default."""
    settings = Settings(environment="development", jwt_secret_key=None)
    assert settings.jwt_secret_key == DEVELOPMENT_JWT_SECRET


def test_staging_settings_without_jwt_secret_raises_validation_error() -> None:
    """Staging must reject missing JWT secrets."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(environment="staging", jwt_secret_key=None)


def test_staging_settings_with_valid_jwt_secret_succeeds() -> None:
    """Staging accepts an explicit JWT secret of sufficient length."""
    settings = Settings(
        environment="staging",
        jwt_secret_key="staging-secret-with-sufficient-length",
    )
    assert settings.jwt_secret_key == "staging-secret-with-sufficient-length"


def test_development_settings_with_explicit_jwt_secret_preserves_value() -> None:
    """Development honors an explicitly supplied JWT secret."""
    settings = Settings(
        environment="development", jwt_secret_key="local-dev-secret-value-1234567890"
    )
    assert settings.jwt_secret_key == "local-dev-secret-value-1234567890"
