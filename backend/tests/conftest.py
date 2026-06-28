"""Shared pytest fixtures."""

import os
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.database import Base, get_db_session
from app.main import app
from app.redis_client import RedisClient, close_redis_client, get_redis_client


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Build test settings."""
    return Settings(
        environment="development",
        debug=True,
        database_url=os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5433/ghost_sweep_test",
        ),
        redis_url=os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1"),
        jwt_secret_key="test-secret-key-with-sufficient-length",
        cors_origins=["http://localhost:3000"],
    )


@pytest_asyncio.fixture
async def db_session(settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def redis_client(settings: Settings) -> AsyncGenerator[RedisClient, None]:
    """Provide a Redis client and flush the test database."""
    client = await get_redis_client(settings)
    await client.flushdb()
    yield client
    await client.flushdb()
    await close_redis_client(client)


@pytest_asyncio.fixture
async def client(
    settings: Settings,
    db_session: AsyncSession,
    redis_client: RedisClient,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP test client with overridden dependencies."""
    app.dependency_overrides[get_settings] = lambda: settings

    async def override_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_redis() -> AsyncGenerator[RedisClient, None]:
        yield redis_client

    app.dependency_overrides[get_db_session] = override_db_session
    from app.dependencies import get_redis

    app.dependency_overrides[get_redis] = override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Generator[None, None, None]:
    """Clear cached settings between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
