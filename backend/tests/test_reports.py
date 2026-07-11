"""Report API tests."""

from uuid import UUID, uuid4

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


async def _create_report(
    client: AsyncClient,
    job_posting_id: str,
    auth_headers: dict[str, str],
    *,
    report_type: ReportType = ReportType.STALE_POSTING,
) -> str:
    """Create a report and return its identifier."""
    response = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": job_posting_id,
            "report_type": report_type.value,
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
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    body = response.json()
    assert response.status_code == 200
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
async def test_get_report_success_for_reporter(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Reporters should be able to read their own pending reports."""
    report_id = await _create_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        report_type=ReportType.NO_RESPONSE,
    )

    response = await client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == report_id


@pytest.mark.asyncio
async def test_get_pending_report_is_hidden_from_public(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Pending reports should not be readable without authorization."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)

    response = await client.get(f"/api/v1/reports/{report_id}")
    assert response.status_code == 404


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
    admin_auth_headers: dict[str, str],
) -> None:
    """Public report list should include only verified reports."""
    report_id = await _create_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        report_type=ReportType.REPOST_LOOP,
    )
    await _verify_report(client, report_id, admin_auth_headers)

    response = await client.get(
        f"/api/v1/reports?job_posting_id={sample_job_posting.id}",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["items"][0]["job_posting_id"] == str(sample_job_posting.id)
    assert "reporter_id" not in body["items"][0]


@pytest.mark.asyncio
async def test_list_reports_supports_pagination(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Public report list should honor page and page_size query parameters."""
    report_ids: list[str] = []
    for report_type in (ReportType.REPOST_LOOP, ReportType.NO_RESPONSE, ReportType.STALE_POSTING):
        report_ids.append(
            await _create_report(
                client,
                str(sample_job_posting.id),
                auth_headers,
                report_type=report_type,
            )
        )
    for report_id in report_ids:
        await _verify_report(client, report_id, admin_auth_headers)

    response = await client.get(
        f"/api/v1/reports?job_posting_id={sample_job_posting.id}&page=1&page_size=2",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
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
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)

    audit_result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "report.created",
            AuditLog.entity_id == UUID(report_id),
        )
    )
    audit_row = audit_result.scalar_one_or_none()
    assert audit_row is not None
    assert audit_row.entity_type == "report"
