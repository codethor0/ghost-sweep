"""Admin moderation API tests."""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import ReportStatus, ReportType, SnapshotEntityType
from app.models.job_posting import JobPosting
from app.models.score_snapshot import ScoreSnapshot

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


@pytest.mark.asyncio
async def test_moderation_list_requires_admin(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Non-admin users should not access the moderation queue."""
    response = await client.get("/api/v1/moderation/reports", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_moderation_list_returns_pending_reports(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Admins should list pending reports for review."""
    await _create_report(client, str(sample_job_posting.id), auth_headers)

    response = await client.get("/api/v1/moderation/reports", headers=admin_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["status"] == ReportStatus.PENDING.value for item in body["items"])


@pytest.mark.asyncio
async def test_verify_report_updates_status(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Admins should verify pending reports."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == ReportStatus.VERIFIED.value


@pytest.mark.asyncio
async def test_dismiss_report_updates_status(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Admins should dismiss pending reports."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=admin_auth_headers,
        json={"reason": "Insufficient evidence for moderation review."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == ReportStatus.DISMISSED.value


@pytest.mark.asyncio
async def test_dismiss_report_writes_reason_to_audit_only(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Dismiss reasons should be stored in audit metadata only."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    reason = "Insufficient evidence for moderation review."
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=admin_auth_headers,
        json={"reason": reason},
    )
    assert response.status_code == 200

    audit = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "report.dismissed",
            AuditLog.entity_id == UUID(report_id),
        )
    )
    assert audit is not None
    assert audit.metadata_json["reason"] == reason


@pytest.mark.asyncio
async def test_verify_dismissed_report_returns_422(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Dismissed reports are terminal and cannot be verified."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    dismiss = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=admin_auth_headers,
    )
    assert dismiss.status_code == 200

    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_verify_disputed_report_succeeds(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
    employer_auth_headers: dict[str, str],
) -> None:
    """Admins should be able to verify disputed reports."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    dispute = await client.post(
        f"/api/v1/reports/{report_id}/responses",
        json={
            "response_text": "This role was actively hiring during the reported period.",
            "evidence_urls": ["https://example.com/hiring-update"],
        },
        headers=employer_auth_headers,
    )
    assert dispute.status_code == 201

    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == ReportStatus.VERIFIED.value


@pytest.mark.asyncio
async def test_verify_report_triggers_score_snapshot(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Verification should recalculate scores and persist snapshots."""
    before_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.COMPANY)
    )
    before_count = int(before_result.scalar_one())

    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200

    after_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.COMPANY)
    )
    after_count = int(after_result.scalar_one())
    assert after_count > before_count


@pytest.mark.asyncio
async def test_verify_missing_report_returns_404(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    """Unknown reports should return 404."""
    response = await client.post(
        f"/api/v1/moderation/reports/{uuid4()}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_verify_report_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Verification should write a report.verified audit log entry."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200

    audit = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "report.verified",
            AuditLog.entity_id == UUID(report_id),
        )
    )
    assert audit is not None
    assert audit.metadata_json["previous_status"] == ReportStatus.PENDING.value
    assert audit.metadata_json["new_status"] == ReportStatus.VERIFIED.value


@pytest.mark.asyncio
async def test_dismiss_report_writes_audit_row(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Dismissal should write a report.dismissed audit log entry."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=admin_auth_headers,
        json={"reason": "Insufficient evidence for moderation review."},
    )
    assert response.status_code == 200

    audit = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "report.dismissed",
            AuditLog.entity_id == UUID(report_id),
        )
    )
    assert audit is not None


@pytest.mark.asyncio
async def test_verify_report_requires_admin(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Non-admin users should not verify reports."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/verify",
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dismiss_report_requires_admin(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Non-admin users should not dismiss reports."""
    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=auth_headers,
        json={"reason": "Insufficient evidence for moderation review."},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dismiss_report_triggers_score_snapshot(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Dismissal should recalculate scores and persist snapshots."""
    before_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    before_count = int(before_result.scalar_one())

    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    response = await client.post(
        f"/api/v1/moderation/reports/{report_id}/dismiss",
        headers=admin_auth_headers,
        json={"reason": "Insufficient evidence for moderation review."},
    )
    assert response.status_code == 200

    after_result = await db_session.execute(
        select(func.count())
        .select_from(ScoreSnapshot)
        .where(ScoreSnapshot.entity_type == SnapshotEntityType.JOB_POSTING)
    )
    after_count = int(after_result.scalar_one())
    assert after_count > before_count
