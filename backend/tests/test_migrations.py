"""Alembic migration verification tests."""

import os

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import build_alembic_config, reset_database_schema

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is not configured",
)

EXPECTED_TABLES = frozenset(
    {
        "alembic_version",
        "audit_logs",
        "companies",
        "employer_claims",
        "employer_responses",
        "evidence_files",
        "job_postings",
        "reports",
        "score_snapshots",
        "users",
        "votes",
    }
)

EXPECTED_ENUM_TYPES = frozenset(
    {
        "claim_status_enum",
        "posting_source_enum",
        "posting_status_enum",
        "report_status_enum",
        "report_type_enum",
        "snapshot_entity_type_enum",
        "verified_status_enum",
        "vote_value_enum",
    }
)


@pytest.fixture(scope="module", autouse=True)
def apply_migrations() -> None:
    """Ensure a clean migrated schema before migration tests run."""
    assert TEST_DATABASE_URL is not None
    reset_database_schema(TEST_DATABASE_URL)


@pytest.mark.asyncio
async def test_alembic_upgrade_head_records_revision() -> None:
    """Applying migrations should record the initial UUID schema revision."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar_one()
    await engine.dispose()
    assert version == "003_audit_remediation"


@pytest.mark.asyncio
async def test_initial_migration_creates_core_tables() -> None:
    """Initial migration should create all Batch 1 entity tables."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        result = await connection.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                """))
        table_names = {row[0] for row in result.fetchall()}
    await engine.dispose()
    assert EXPECTED_TABLES.issubset(table_names)


@pytest.mark.asyncio
async def test_initial_migration_creates_postgresql_enum_types() -> None:
    """Initial migration should create native PostgreSQL ENUM types."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        result = await connection.execute(
            text("""
                SELECT typname
                FROM pg_type
                WHERE typname = ANY(:enum_names)
                """),
            {"enum_names": list(EXPECTED_ENUM_TYPES)},
        )
        enum_names = {row[0] for row in result.fetchall()}
    await engine.dispose()
    assert enum_names == EXPECTED_ENUM_TYPES


@pytest.mark.asyncio
async def test_votes_table_has_unique_report_user_constraint() -> None:
    """Votes must enforce one vote per user per report."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        result = await connection.execute(text("""
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_votes_report_user'
                  AND contype = 'u'
                """))
        constraint_exists = result.first() is not None
    await engine.dispose()
    assert constraint_exists is True


@pytest.mark.asyncio
async def test_employer_claims_have_partial_unique_indexes() -> None:
    """Employer claims should enforce one approved claim per company and one pending per user."""
    assert TEST_DATABASE_URL is not None
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.connect() as connection:
        result = await connection.execute(text("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND indexname IN (
                    'uq_employer_claims_company_approved',
                    'uq_employer_claims_user_company_pending'
                  )
                """))
        index_names = {row[0] for row in result.fetchall()}
    await engine.dispose()
    assert index_names == {
        "uq_employer_claims_company_approved",
        "uq_employer_claims_user_company_pending",
    }


def test_downgrade_and_upgrade_cycle_succeeds() -> None:
    """Downgrade and upgrade should cleanly remove and recreate schema objects."""
    assert TEST_DATABASE_URL is not None
    alembic_config = build_alembic_config(TEST_DATABASE_URL)
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
