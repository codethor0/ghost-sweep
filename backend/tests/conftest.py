"""Pytest configuration and database fixtures for backend tests."""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def build_alembic_config(database_url: str) -> Config:
    """Build an Alembic config for the supplied database URL.

    Args:
        database_url: Async SQLAlchemy database URL.

    Returns:
        Config: Alembic configuration object.
    """
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    return alembic_config


def run_migrations_to_head(database_url: str) -> None:
    """Apply all Alembic migrations to the supplied database URL.

    Args:
        database_url: Async SQLAlchemy database URL.
    """
    command.upgrade(build_alembic_config(database_url), "head")


async def _recreate_public_schema(database_url: str) -> None:
    """Drop and recreate the public schema for a clean migration baseline.

    Args:
        database_url: Async SQLAlchemy database URL.
    """
    engine = create_async_engine(database_url, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
        await connection.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
    await engine.dispose()


def reset_database_schema(database_url: str) -> None:
    """Reset the database schema by recreating public and upgrading to head.

    Args:
        database_url: Async SQLAlchemy database URL.
    """
    asyncio.run(_recreate_public_schema(database_url))
    alembic_config = build_alembic_config(database_url)
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Provide the configured integration test database URL.

    Returns:
        str: PostgreSQL URL for integration tests.

    Raises:
        pytest.SkipTest: When TEST_DATABASE_URL is not configured.
    """
    if TEST_DATABASE_URL is None:
        pytest.skip("TEST_DATABASE_URL is not configured")
    return TEST_DATABASE_URL


@pytest.fixture(scope="session")
def migrated_database(test_database_url: str) -> str:
    """Apply migrations once per test session.

    Args:
        test_database_url: Integration test database URL.

    Returns:
        str: Database URL with migrations applied.
    """
    run_migrations_to_head(test_database_url)
    return test_database_url


@pytest_asyncio.fixture
async def db_session(migrated_database: str) -> AsyncGenerator[AsyncSession, None]:
    """Provide a request-scoped async database session.

    Args:
        migrated_database: Database URL with migrations applied.

    Yields:
        AsyncSession: Active SQLAlchemy session rolled back after each test.
    """
    engine = create_async_engine(migrated_database, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()
