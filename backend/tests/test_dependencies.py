"""FastAPI dependency tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings_dependency


@pytest.mark.asyncio
async def test_get_settings_dependency_returns_cached_settings() -> None:
    """Settings dependency should return the cached settings instance."""
    settings = await get_settings_dependency()
    assert isinstance(settings, Settings)
    assert settings.app_name == "ghost-sweep"


@pytest.mark.asyncio
async def test_get_db_yields_session_from_factory() -> None:
    """Database dependency should yield the session provided by the factory."""
    mock_session = AsyncMock(spec=AsyncSession)

    async def mock_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield mock_session

    with patch("app.dependencies.get_db_session", mock_get_db_session):
        generator = get_db()
        session = await anext(generator)
        assert session is mock_session

        with pytest.raises(StopAsyncIteration):
            await anext(generator)
