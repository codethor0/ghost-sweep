"""FastAPI dependencies for request scope resources."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db_session


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
