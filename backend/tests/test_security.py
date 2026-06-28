"""Security utility tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.config import get_settings
from app.exceptions import UnauthorizedError
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, decode_access_token


def test_hash_password_returns_bcrypt_hash() -> None:
    """Password hashing should return a bcrypt hash."""
    password_hash = hash_password("StrongPass123!")
    assert password_hash.startswith("$2")


def test_verify_password_accepts_correct_password() -> None:
    """Password verification should accept the original password."""
    password = "StrongPass123!"
    password_hash = hash_password(password)
    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_wrong_password() -> None:
    """Password verification should reject an incorrect password."""
    password_hash = hash_password("StrongPass123!")
    assert verify_password("WrongPass123!", password_hash) is False


def test_create_and_decode_access_token() -> None:
    """Access tokens should round-trip through create and decode."""
    settings = get_settings()
    subject = uuid4()
    token = create_access_token(subject, settings)
    assert decode_access_token(token, settings) == str(subject)


def test_decode_access_token_rejects_expired_token() -> None:
    """Expired access tokens should raise UnauthorizedError."""
    settings = get_settings()
    assert settings.jwt_secret_key is not None
    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(tz=UTC) - timedelta(minutes=1),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(UnauthorizedError):
        decode_access_token(token, settings)


def test_decode_access_token_rejects_wrong_token_type() -> None:
    """Non-access tokens should raise UnauthorizedError."""
    settings = get_settings()
    assert settings.jwt_secret_key is not None
    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(tz=UTC) + timedelta(minutes=15),
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(UnauthorizedError):
        decode_access_token(token, settings)
