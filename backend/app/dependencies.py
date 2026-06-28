"""FastAPI dependencies."""

from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session
from app.exceptions import UnauthorizedError
from app.models.user import User
from app.redis_client import RedisClient, close_redis_client, get_redis_client
from app.security.tokens import decode_token


async def get_settings_dependency() -> Settings:
    """Provide application settings.

    Returns:
        Settings: Cached settings instance.
    """
    return get_settings()


async def get_redis(
    settings: Settings = Depends(get_settings_dependency),
) -> AsyncGenerator[RedisClient, None]:
    """Provide a Redis client for request scope.

    Args:
        settings: Application settings.

    Yields:
        RedisClient: Async Redis client.
    """
    client = await get_redis_client(settings)
    try:
        yield client
    finally:
        await close_redis_client(client)


async def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings_dependency),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Resolve the authenticated user from a bearer token.

    Args:
        authorization: Authorization header value.
        settings: Application settings.
        session: Database session.

    Returns:
        User: Authenticated user record.

    Raises:
        UnauthorizedError: When the token is missing or invalid.
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise UnauthorizedError()

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(settings, token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError() from exc

    if payload.get("type") != "access":
        raise UnauthorizedError()

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError()

    result = await session.execute(
        select(User).where(User.id == int(user_id), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError()
    return user


async def enforce_auth_rate_limit(
    request: Request,
    redis: RedisClient = Depends(get_redis),
    settings: Settings = Depends(get_settings_dependency),
) -> None:
    """Apply a simple Redis-backed rate limit to auth endpoints.

    Args:
        request: Incoming HTTP request.
        redis: Redis client.
        settings: Application settings.

    Raises:
        UnauthorizedError: When the rate limit is exceeded.
    """
    client_host = request.client.host if request.client else "unknown"
    key = f"auth-rate:{client_host}"
    current_count = await redis.incr(key)
    if current_count == 1:
        await redis.expire(key, 60)
    if current_count > settings.auth_rate_limit_per_minute:
        raise UnauthorizedError("Too many authentication attempts")
