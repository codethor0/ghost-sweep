"""Redis-backed opaque refresh token storage."""

import hashlib
import secrets
from uuid import UUID

from app.config import Settings
from app.redis_client import RedisClient

_CONSUME_REFRESH_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if value then
  redis.call('DEL', KEYS[1])
end
return value
"""


def hash_refresh_token(token: str) -> str:
    """Return the SHA-256 hex digest for a refresh token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_key(token_hash: str) -> str:
    """Build the Redis key for a refresh token hash."""
    return f"refresh:{token_hash}"


async def issue_refresh_token(redis: RedisClient, user_id: UUID, settings: Settings) -> str:
    """Issue an opaque refresh token and store its hash in Redis."""
    token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(token)
    ttl_seconds = settings.refresh_token_expire_days * 86400
    await redis.set(refresh_token_key(token_hash), str(user_id), ex=ttl_seconds)
    return token


async def consume_refresh_token(redis: RedisClient, token: str) -> UUID | None:
    """Atomically validate and revoke a refresh token."""
    token_hash = hash_refresh_token(token)
    user_id = await redis.eval(  # type: ignore[no-untyped-call]
        _CONSUME_REFRESH_SCRIPT,
        1,
        refresh_token_key(token_hash),
    )
    if user_id is None:
        return None
    try:
        return UUID(str(user_id))
    except ValueError:
        return None


async def validate_refresh_token(redis: RedisClient, token: str) -> UUID | None:
    """Validate a refresh token without consuming it."""
    token_hash = hash_refresh_token(token)
    stored_user_id = await redis.get(refresh_token_key(token_hash))
    if stored_user_id is None:
        return None
    try:
        return UUID(stored_user_id)
    except ValueError:
        return None


async def revoke_refresh_token(redis: RedisClient, token: str) -> None:
    """Revoke a refresh token by deleting its Redis entry."""
    token_hash = hash_refresh_token(token)
    await redis.delete(refresh_token_key(token_hash))


async def rotate_refresh_token(
    redis: RedisClient,
    token: str,
    settings: Settings,
) -> tuple[UUID, str] | None:
    """Consume an existing refresh token and issue a replacement."""
    user_id = await consume_refresh_token(redis, token)
    if user_id is None:
        return None
    new_token = await issue_refresh_token(redis, user_id, settings)
    return user_id, new_token
