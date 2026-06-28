"""JWT access token creation and validation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.config import Settings
from app.exceptions import UnauthorizedError

ACCESS_TOKEN_CLAIM_TYPE = "access"  # nosec B105


def create_access_token(subject: UUID | str, settings: Settings) -> str:
    """Create a signed JWT access token.

    Args:
        subject: User identifier stored in the token subject claim.
        settings: Application settings containing JWT configuration.

    Returns:
        str: Encoded JWT access token.

    Raises:
        UnauthorizedError: When JWT settings are not configured.
    """
    if settings.jwt_secret_key is None:
        raise UnauthorizedError()

    expire = datetime.now(tz=UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(tz=UTC),
        "jti": str(uuid4()),
        "type": ACCESS_TOKEN_CLAIM_TYPE,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> str:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT access token.
        settings: Application settings containing JWT configuration.

    Returns:
        str: Token subject containing the user identifier.

    Raises:
        UnauthorizedError: When the token is invalid, expired, or not an access token.
    """
    if settings.jwt_secret_key is None:
        raise UnauthorizedError()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError() from exc

    token_type = payload.get("type")
    subject = payload.get("sub")
    if token_type != ACCESS_TOKEN_CLAIM_TYPE or subject is None:
        raise UnauthorizedError()

    return str(subject)
