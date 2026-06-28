"""Report API tests."""

from uuid import uuid4

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import ReportType
from app.models.job_posting import JobPosting


REPORT_DESCRIPTION = (
    "The posting remained active for several months without recruiter follow-up or status updates."
)


@pytest.mark.asyncio
async def test_create_report_requires_auth(
    client: AsyncClient, sample_job_posting: JobPosting
) -> None:
    """Report creation should require authentication."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.STALE_POSTING.value,
            "description": REPORT_DESCRIPTION,
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_report_success(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Authenticated users should be able to submit reports."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.STALE_POSTING.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["job_posting_id"] == str(sample_job_posting.id)
    assert body["report_type"] == ReportType.STALE_POSTING.value
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_create_report_unknown_job_posting_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Reports for unknown postings should return 404."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(uuid4()),
            "report_type": ReportType.STALE_POSTING.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_report_success(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Report detail should return a submitted report."""
    create_response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.NO_RESPONSE.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    report_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["id"] == report_id


@pytest.mark.asyncio
async def test_get_report_returns_404_for_missing_id(client: AsyncClient) -> None:
    """Unknown reports should return 404."""
    response = await client.get(f"/api/v1/reports/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_reports_filtered_by_job_posting_id(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Report list should filter by job posting identifier."""
    await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.REPOST_LOOP.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )

    response = await client.get(
        f"/api/v1/reports?job_posting_id={sample_job_posting.id}",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert all(item["job_posting_id"] == str(sample_job_posting.id) for item in body["items"])


@pytest.mark.asyncio
async def test_list_reports_supports_pagination(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Report list should honor page and page_size query parameters."""
    for report_type in (ReportType.REPOST_LOOP, ReportType.NO_RESPONSE, ReportType.STALE_POSTING):
        await client.post(
            "/api/v1/reports",
            json={
                "job_posting_id": str(sample_job_posting.id),
                "report_type": report_type.value,
                "description": REPORT_DESCRIPTION,
            },
            headers=auth_headers,
        )

    response = await client.get(
        f"/api/v1/reports?job_posting_id={sample_job_posting.id}&page=1&page_size=2",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2


@pytest.mark.asyncio
async def test_create_report_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Report creation should write an audit log entry."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.STALE_POSTING.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    report_id = response.json()["id"]

    audit_result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "report.created",
            AuditLog.entity_id == UUID(report_id),
        )
    )
    audit_row = audit_result.scalar_one_or_none()
    assert audit_row is not None
    assert audit_row.entity_type == "report"
