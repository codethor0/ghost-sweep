"""JWT token creation and validation."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import jwt

from app.config import Settings


def create_access_token(settings: Settings, subject: str) -> str:
    """Create a signed JWT access token.

    Args:
        settings: Application settings.
        subject: Token subject, typically user id as string.

    Returns:
        str: Encoded JWT access token.
    """
    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(settings: Settings, subject: str) -> tuple[str, str]:
    """Create a refresh token and its identifier.

    Args:
        settings: Application settings.
        subject: Token subject, typically user id as string.

    Returns:
        tuple[str, str]: Encoded refresh token and token identifier.
    """
    token_id = str(uuid4())
    expire = datetime.now(tz=UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": token_id}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, token_id


def decode_token(settings: Settings, token: str) -> dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        settings: Application settings.
        token: Encoded JWT token.

    Returns:
        dict[str, Any]: Decoded token payload.

    Raises:
        jwt.PyJWTError: When the token is invalid or expired.
    """
    return cast(
        dict[str, Any],
        jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]),
    )
