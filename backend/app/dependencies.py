"""FastAPI dependencies for request scope resources."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.redis_client import RedisClient, get_shared_redis_client
from app.security.tokens import decode_access_token
from app.services.auth import get_user_by_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_settings_dependency() -> Settings:
    """Provide application settings.

    Returns:
        Settings: Cached settings instance.
    """
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session.

    Yields:
        AsyncSession: Request-scoped SQLAlchemy session.
    """
    async for session in get_db_session():
        yield session


async def get_redis() -> AsyncGenerator[RedisClient, None]:
    """Provide the shared application Redis client.

    Yields:
        RedisClient: Shared async Redis client.
    """
    yield get_shared_redis_client()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> User:
    """Load the authenticated user from a bearer access token.

    Args:
        credentials: Parsed Authorization header credentials.
        session: Active database session.
        settings: Application settings.

    Returns:
        User: Authenticated user record.

    Raises:
        UnauthorizedError: When the token is missing, invalid, or expired.
    """
    if credentials is None:
        raise UnauthorizedError()

    subject = decode_access_token(credentials.credentials, settings)
    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise UnauthorizedError() from exc

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedError()

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require an authenticated admin user.

    Args:
        current_user: Authenticated user from bearer token.

    Returns:
        User: Admin user record.

    Raises:
        ForbiddenError: When the user is not an admin.
    """
    if not current_user.is_admin:
        raise ForbiddenError()
    return current_user
