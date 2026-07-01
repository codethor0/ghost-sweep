"""Employer response API tests."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.enums import ReportStatus, ReportType, SnapshotEntityType, VerifiedStatus
from app.models.job_posting import JobPosting
from app.models.score_snapshot import ScoreSnapshot

REPORT_DESCRIPTION = (
    "The posting remained active for several months without recruiter follow-up or status updates."
)
RESPONSE_TEXT = "This role remained open while active interviews were scheduled with candidates."


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


@pytest.mark.asyncio
async def test_create_employer_response_requires_auth(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Employer responses should require authentication."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_employer_response_requires_verified_employer(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Non-employer users should not submit employer responses."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    suffix = uuid4().hex[:8]
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other-{suffix}@example.com",
            "username": f"other_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 200
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_employer_response_wrong_company_returns_403(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Verified employers cannot respond to reports for another company's posting."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)

    other_company = Company(
        name=f"Other Corp {uuid4().hex[:8]}",
        domain="other.example.com",
        industry="Technology",
        size="1-50",
        locations=["Remote"],
        integrity_score=Decimal("50.0"),
        verified_status=VerifiedStatus.UNVERIFIED,
        total_postings=0,
        total_hires=0,
        report_count=0,
    )
    db_session.add(other_company)
    await db_session.flush()

    suffix = uuid4().hex[:8]
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other-employer-{suffix}@example.com",
            "username": f"other_employer_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert register.status_code == 200
    employer_headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    claim = await client.post(
        "/api/v1/employer-claims",
        json={
            "company_id": str(other_company.id),
            "verification_documents": ["https://example.com/other-verify.txt"],
        },
        headers=employer_headers,
    )
    assert claim.status_code == 201

    approve = await client.post(
        f"/api/v1/employer-claims/{claim.json()['id']}/approve",
        headers=admin_auth_headers,
    )
    assert approve.status_code == 200

    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_employer_response_rejects_javascript_evidence_url(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Evidence URLs must use http or https schemes."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={
            "response_text": RESPONSE_TEXT,
            "evidence_urls": ["javascript:alert(1)"],
        },
        headers=employer_auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_employer_response_disputes_pending_report(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Employer responses should move pending reports to disputed."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={
            "response_text": RESPONSE_TEXT,
            "evidence_urls": ["https://example.com/hiring-proof"],
        },
        headers=employer_auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["report_id"] == report_id

    report = await client.get(f"/api/v1/reports/{report_id}")
    assert report.status_code == 200
    assert report.json()["status"] == ReportStatus.DISPUTED.value


@pytest.mark.asyncio
async def test_create_multiple_employer_responses_allowed(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Multiple employer responses should be allowed on the same report."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    first = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_auth_headers,
    )
    assert first.status_code == 201

    second = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": "We posted an additional clarification for candidates."},
        headers=employer_auth_headers,
    )
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.asyncio
async def test_list_employer_responses_is_public(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Employer responses should be readable without authentication."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    create = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_auth_headers,
    )
    assert create.status_code == 201

    response = await client.get(f"/api/v1/reports/{report_id}/responses")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["response_text"] == RESPONSE_TEXT


@pytest.mark.asyncio
async def test_create_employer_response_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Employer response creation should write an audit log entry."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_auth_headers,
    )
    response_id = response.json()["id"]

    audit = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "employer_response.created",
            AuditLog.entity_id == UUID(response_id),
        )
    )
    assert audit is not None
    assert audit.metadata_json["previous_status"] == ReportStatus.PENDING.value
    assert audit.metadata_json["new_status"] == ReportStatus.DISPUTED.value


@pytest.mark.asyncio
async def test_create_employer_response_triggers_score_snapshot(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Employer responses should recalculate scores and persist snapshots."""
    before_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    before_count = int(before_result.scalar_one())

    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_auth_headers,
    )
    assert response.status_code == 201

    after_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    after_count = int(after_result.scalar_one())
    assert after_count > before_count


@pytest.mark.asyncio
async def test_create_employer_response_unknown_report_returns_404(
    client: AsyncClient,
    employer_auth_headers: dict[str, str],
) -> None:
    """Responses for missing reports should return 404."""
    response = await client.post(
        f"/api/v1/reports/{uuid4()}/responses",
        json={"response_text": RESPONSE_TEXT},
        headers=employer_auth_headers,
    )
    assert response.status_code == 404
