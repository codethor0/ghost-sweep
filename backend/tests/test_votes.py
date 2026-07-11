"""Vote API tests."""

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_errors import VOTE_REPORT_USER_UNIQUE
from app.exceptions import ConflictError
from app.models.audit_log import AuditLog
from app.models.enums import ReportType, SnapshotEntityType, VoteValue
from app.models.job_posting import JobPosting
from app.models.score_snapshot import ScoreSnapshot
from app.models.user import User
from app.schemas import CreateVoteRequest
from app.services import votes as votes_service

REPORT_DESCRIPTION = (
    "The posting remained active for several months without recruiter follow-up or status updates."
)


async def _create_report(
    client: AsyncClient,
    job_posting_id: str,
    auth_headers: dict[str, str],
) -> str:
    """Create a report and return its identifier."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": job_posting_id,
            "report_type": ReportType.STALE_POSTING.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return str(response.json()["id"])


async def _verify_report(
    client: AsyncClient,
    report_id: str,
    admin_auth_headers: dict[str, str],
) -> None:
    """Verify a report through the moderation API."""
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200


async def _create_verified_report(
    client: AsyncClient,
    job_posting_id: str,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> str:
    """Create and verify a report for public vote tests."""
    report_id = await _create_report(client, job_posting_id, auth_headers)
    await _verify_report(client, report_id, admin_auth_headers)
    return report_id


@pytest.mark.asyncio
async def test_create_vote_requires_auth(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Vote creation should require authentication."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.UP.value},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_vote_success(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Authenticated users should be able to vote on verified reports."""
    report_id = await _create_verified_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        admin_auth_headers,
    )
    response = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.UP.value},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["report_id"] == report_id
    assert body["vote"] == VoteValue.UP.value


@pytest.mark.asyncio
async def test_create_duplicate_vote_returns_409(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Duplicate votes by the same user should return 409."""
    report_id = await _create_verified_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        admin_auth_headers,
    )
    first = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.UP.value},
        headers=auth_headers,
    )
    assert first.status_code == 201

    duplicate = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.DOWN.value},
        headers=auth_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Vote already recorded for this report"


@pytest.mark.asyncio
async def test_create_vote_handles_integrity_error_on_flush(
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
    client: AsyncClient,
) -> None:
    """Duplicate vote races should return conflict instead of 500."""
    report_id = await _create_verified_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        admin_auth_headers,
    )
    me_response = await client.get("/api/v1/auth/me", headers=auth_headers)
    voter = User(id=me_response.json()["id"])

    async def flush_with_integrity_error(*_args: object, **_kwargs: object) -> None:
        orig = MagicMock()
        orig.diag.constraint_name = VOTE_REPORT_USER_UNIQUE
        raise IntegrityError("INSERT", {}, orig)

    db_session.flush = flush_with_integrity_error  # type: ignore[method-assign]

    with pytest.raises(ConflictError, match="Vote already recorded"):
        await votes_service.create_vote(
            db_session,
            report_id=UUID(report_id),
            payload=CreateVoteRequest(vote=VoteValue.UP),
            voter=voter,
        )


@pytest.mark.asyncio
async def test_create_vote_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Vote creation should write an audit log entry."""
    report_id = await _create_verified_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        admin_auth_headers,
    )
    response = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.UP.value},
        headers=auth_headers,
    )
    vote_id = response.json()["id"]

    audit_result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "vote.created",
            AuditLog.entity_id == UUID(vote_id),
        )
    )
    audit_row = audit_result.scalar_one_or_none()
    assert audit_row is not None
    assert audit_row.entity_type == "vote"


@pytest.mark.asyncio
async def test_create_vote_triggers_score_snapshot(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Vote creation should persist score snapshots for posting and company."""
    before_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    before_count = int(before_result.scalar_one())

    report_id = await _create_verified_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        admin_auth_headers,
    )
    vote_response = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": VoteValue.UP.value},
        headers=auth_headers,
    )
    assert vote_response.status_code == 201

    after_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    after_count = int(after_result.scalar_one())
    assert after_count > before_count
