"""Pytest configuration and database fixtures for backend tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import Settings, get_settings
from app.dependencies import get_db, get_redis, get_settings_dependency
from app.main import app
from app.models.company import Company
from app.models.enums import PostingSource, PostingStatus, VerifiedStatus
from app.models.job_posting import JobPosting
from app.models.user import User
from app.redis_client import (
    RedisClient,
    close_redis_client,
    get_redis_client,
    init_redis_client,
    shutdown_redis_client,
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")


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
def test_redis_url() -> str:
    """Provide the configured integration test Redis URL.

    Returns:
        str: Redis URL for integration tests.

    Raises:
        pytest.SkipTest: When TEST_REDIS_URL is not configured.
    """
    if TEST_REDIS_URL is None:
        pytest.skip("TEST_REDIS_URL is not configured")
    return TEST_REDIS_URL


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
    async with engine.connect() as connection:
        await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def redis_client(test_redis_url: str) -> AsyncGenerator[RedisClient, None]:
    """Provide a Redis client backed by the integration test database.

    Args:
        test_redis_url: Integration test Redis URL.

    Yields:
        RedisClient: Active Redis client with a flushed database after each test.
    """
    settings = Settings(redis_url=test_redis_url)
    client = await get_redis_client(settings)
    try:
        yield client
    finally:
        await client.flushdb()
        await close_redis_client(client)


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    redis_client: RedisClient,
) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client with database and Redis dependencies overridden.

    Args:
        db_session: Request-scoped database session.
        redis_client: Request-scoped Redis client.

    Yields:
        AsyncClient: Async HTTP client bound to the FastAPI application.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis() -> AsyncIterator[RedisClient]:
        yield redis_client

    async def override_get_settings() -> Settings:
        return get_settings()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    app.dependency_overrides[get_settings_dependency] = override_get_settings

    await init_redis_client(get_settings())
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        app.dependency_overrides.clear()
        await shutdown_redis_client()


@pytest_asyncio.fixture
async def sample_company(db_session: AsyncSession) -> Company:
    """Provide a persisted company for domain API tests."""
    company = Company(
        name=f"Integrity Corp {uuid4().hex[:8]}",
        domain="example.com",
        industry="Technology",
        size="100-500",
        locations=["Remote"],
        integrity_score=Decimal("50.0"),
        verified_status=VerifiedStatus.UNVERIFIED,
        total_postings=1,
        total_hires=0,
        report_count=0,
    )
    db_session.add(company)
    await db_session.flush()
    return company


@pytest_asyncio.fixture
async def sample_job_posting(db_session: AsyncSession, sample_company: Company) -> JobPosting:
    """Provide a persisted job posting for domain API tests."""
    now = datetime.now(tz=UTC)
    posting = JobPosting(
        company_id=sample_company.id,
        title="Platform Engineer",
        description="Build integrity tooling.",
        url=f"https://example.com/jobs/{uuid4()}",
        source=PostingSource.COMPANY_SITE,
        posted_date=now,
        status=PostingStatus.ACTIVE,
        ghost_risk_score=Decimal("50.0"),
        repost_count=0,
        detected_at=now,
        last_seen_at=now,
    )
    db_session.add(posting)
    await db_session.flush()
    return posting


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Provide bearer auth headers for an registered test user."""
    suffix = uuid4().hex[:8]
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"voter-{suffix}@example.com",
            "username": f"voter_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    """Provide bearer auth headers for a registered admin user."""
    suffix = uuid4().hex[:8]
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"admin-{suffix}@example.com",
            "username": f"admin_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = UUID(me_response.json()["id"])
    await db_session.execute(update(User).where(User.id == user_id).values(is_admin=True))
    await db_session.flush()
    return headers


@pytest_asyncio.fixture
async def employer_auth_headers(
    client: AsyncClient,
    sample_company: Company,
    admin_auth_headers: dict[str, str],
) -> dict[str, str]:
    """Provide bearer auth headers for an approved employer on sample_company."""
    suffix = uuid4().hex[:8]
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"employer-{suffix}@example.com",
            "username": f"employer_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 200
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    claim = await client.post(
        "/api/v1/employer-claims",
        json={
            "company_id": str(sample_company.id),
            "verification_documents": ["https://example.com/verify.txt"],
        },
        headers=headers,
    )
    assert claim.status_code == 201
    claim_id = claim.json()["id"]

    approve = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=admin_auth_headers,
    )
    assert approve.status_code == 200
    return headers
