"""Redis-backed opaque refresh token storage."""

import hashlib
import secrets
from uuid import UUID

from app.config import Settings
from app.redis_client import RedisClient


def hash_refresh_token(token: str) -> str:
    """Return the SHA-256 hex digest for a refresh token.

    Args:
        token: Opaque refresh token.

    Returns:
        str: Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_key(token_hash: str) -> str:
    """Build the Redis key for a refresh token hash.

    Args:
        token_hash: SHA-256 hex digest of the refresh token.

    Returns:
        str: Redis key in the form refresh:{token_hash}.
    """
    return f"refresh:{token_hash}"


async def issue_refresh_token(redis: RedisClient, user_id: UUID, settings: Settings) -> str:
    """Issue an opaque refresh token and store its hash in Redis.

    Args:
        redis: Active Redis client.
        user_id: User UUID associated with the token.
        settings: Application settings.

    Returns:
        str: Opaque refresh token for the client.
    """
    token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(token)
    ttl_seconds = settings.refresh_token_expire_days * 86400
    await redis.set(refresh_token_key(token_hash), str(user_id), ex=ttl_seconds)
    return token


async def validate_refresh_token(redis: RedisClient, token: str) -> UUID | None:
    """Validate a refresh token against Redis storage.

    Args:
        redis: Active Redis client.
        token: Opaque refresh token from the client.

    Returns:
        UUID | None: Associated user UUID when the token is valid.
    """
    token_hash = hash_refresh_token(token)
    user_id = await redis.get(refresh_token_key(token_hash))
    if user_id is None:
        return None
    try:
        return UUID(user_id)
    except ValueError:
        return None


async def revoke_refresh_token(redis: RedisClient, token: str) -> None:
    """Revoke a refresh token by deleting its Redis entry.

    Args:
        redis: Active Redis client.
        token: Opaque refresh token from the client.
    """
    token_hash = hash_refresh_token(token)
    await redis.delete(refresh_token_key(token_hash))
