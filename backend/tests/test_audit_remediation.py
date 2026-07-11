"""Regression tests for independent deep-audit remediation."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.enums import ReportType
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.security.password_policy import BCRYPT_MAX_PASSWORD_BYTES, validate_password_byte_length
from app.services.job_url_validation import (
    JobSourceProvider,
    extract_employer_identity,
    validate_job_url,
)
from app.services.sheet_import import _map_posting_source, check_eligibility, resolve_column_map
from tests.test_reports import REPORT_DESCRIPTION, _create_report, _verify_report

DEFAULT_PASSWORD = "StrongPass123!"


def test_password_byte_limit_rejects_multibyte_overflow() -> None:
    """Passwords above bcrypt's UTF-8 byte boundary should be rejected."""
    password = "a" * 70 + "éé"
    assert len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES
    with pytest.raises(ValueError, match="UTF-8 bytes"):
        validate_password_byte_length(password)


@pytest.mark.asyncio
async def test_pending_report_does_not_change_company_score(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Creating a pending report must not change the public company score."""
    company = await db_session.get(Company, sample_job_posting.company_id)
    assert company is not None
    before = float(company.integrity_score)

    await _create_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        report_type=ReportType.NO_RESPONSE,
    )
    await db_session.refresh(company)
    assert float(company.integrity_score) == before


@pytest.mark.asyncio
async def test_duplicate_report_submission_returns_409(
    client: AsyncClient,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
) -> None:
    """Duplicate active reports from the same account should conflict."""
    await _create_report(
        client,
        str(sample_job_posting.id),
        auth_headers,
        report_type=ReportType.NO_RESPONSE,
    )
    duplicate = await client.post(
        "/api/v1/reports",
        json={
            "job_posting_id": str(sample_job_posting.id),
            "report_type": ReportType.NO_RESPONSE.value,
            "description": REPORT_DESCRIPTION,
        },
        headers=auth_headers,
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_verified_report_updates_verification_votes(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_job_posting: JobPosting,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Votes on verified reports should update report.verification_votes."""
    suffix = uuid4().hex[:8]
    voter_register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"voter-{suffix}@example.com",
            "username": f"voter_{suffix}",
            "password": DEFAULT_PASSWORD,
        },
    )
    voter_headers = {"Authorization": f"Bearer {voter_register.json()['access_token']}"}

    report_id = await _create_report(client, str(sample_job_posting.id), auth_headers)
    await _verify_report(client, report_id, admin_auth_headers)

    vote = await client.post(
        f"/api/v1/reports/{report_id}/votes",
        json={"vote": "up"},
        headers=voter_headers,
    )
    assert vote.status_code == 201

    report = await db_session.scalar(select(Report).where(Report.id == report_id))
    assert report is not None
    assert report.verification_votes == 1


@pytest.mark.asyncio
async def test_register_rejects_case_equivalent_email(
    client: AsyncClient,
) -> None:
    """Email uniqueness should be case-insensitive."""
    suffix = uuid4().hex[:8]
    first = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"Case-{suffix}@Example.com",
            "username": f"case_user_{suffix}",
            "password": DEFAULT_PASSWORD,
        },
    )
    assert first.status_code == 200

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"case-{suffix}@example.com",
            "username": f"case_user2_{suffix}",
            "password": DEFAULT_PASSWORD,
        },
    )
    assert duplicate.status_code == 409


def test_supported_ats_providers_do_not_map_to_other() -> None:
    """Supported ATS providers should not be classified as OTHER in sheet import."""
    urls = {
        JobSourceProvider.ICIMS: "https://careers-acme.icims.com/jobs/1234/job",
        JobSourceProvider.WORKABLE: "https://apply.workable.com/acme/j/ABC123DEF4",
        JobSourceProvider.BAMBOOHR: "https://acme.bamboohr.com/careers/42",
        JobSourceProvider.TALEO: "https://acme.taleo.net/careersection/jobdetail.ftl?job=123",
        JobSourceProvider.JOBVITE: "https://jobs.jobvite.com/acme/job/oUZbYfwF",
    }
    for provider, url in urls.items():
        normalized = validate_job_url(url).normalized_url
        assert normalized is not None
        assert validate_job_url(url).provider == provider
        assert _map_posting_source(normalized).value == "company_site"


def test_extract_employer_identity_avoids_shared_ats_domain() -> None:
    """Hosted ATS URLs should not use the shared platform host as company domain."""
    normalized = validate_job_url("https://boards.greenhouse.io/acme/jobs/1234567").normalized_url
    assert normalized is not None
    identity = extract_employer_identity(normalized)
    assert identity.tenant_identifier == "acme"
    assert identity.company_domain_hint is None


def test_sheet_import_requires_reviewer_and_reviewed_at() -> None:
    """Import-ready rows must include reviewer and reviewed_at."""
    headers = [
        "Timestamp",
        "Job posting URL",
        "Company name",
        "Job title",
        "Location or remote",
        "Date seen",
        "Why do you suspect this is a ghost job?",
        "Has the company responded?",
        "Consent",
        "Evidence links",
        "Optional contact email",
        "review_status",
        "reviewer",
        "reviewed_at",
        "decline_reason_code",
        "duplicate_of",
        "notes",
        "pii_redacted",
        "import_ready",
        "escalation_level",
    ]
    column_map = resolve_column_map(headers)
    row = {
        "Timestamp": "2026-07-01 12:00:00",
        "Job posting URL": "https://boards.greenhouse.io/acme/jobs/1234567",
        "Company name": "Acme Corp",
        "Job title": "Software Engineer",
        "Location or remote": "Remote",
        "Date seen": "2026-06-30",
        "Why do you suspect this is a ghost job?": (
            "Listing has been open for months with no hiring updates."
        ),
        "Has the company responded?": "No",
        "Consent": "I confirm this submission is made in good faith.",
        "Evidence links": "",
        "Optional contact email": "",
        "review_status": "approved_for_import",
        "reviewer": "",
        "reviewed_at": "",
        "decline_reason_code": "",
        "duplicate_of": "",
        "notes": "",
        "pii_redacted": "yes",
        "import_ready": "yes",
        "escalation_level": "none",
    }
    result = check_eligibility(row, column_map)
    assert result.eligible is False
    assert result.reason_code == "missing_reviewer"


@pytest.mark.asyncio
async def test_readiness_endpoint_reports_dependency_status(client: AsyncClient) -> None:
    """Readiness endpoint should report PostgreSQL and Redis status."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["postgres"] == "ok"
    assert body["checks"]["redis"] == "ok"
