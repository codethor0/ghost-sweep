"""Job posting endpoint tests."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.job_posting import JobPosting


@pytest.mark.asyncio
async def test_get_job_posting_risk_score_returns_transparent_breakdown(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Risk score endpoint should return weighted components and explanation."""
    company = Company(name="Example Corp")
    db_session.add(company)
    await db_session.flush()

    now = datetime.now(tz=UTC)
    posting = JobPosting(
        company_id=company.id,
        title="Backend Engineer",
        posting_url="https://example.com/jobs/backend-engineer",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(posting)
    await db_session.commit()

    response = await client.get(f"/api/v1/job-postings/{posting.id}/risk-score")
    assert response.status_code == 200
    body = response.json()
    assert body["job_posting_id"] == posting.id
    assert "components" in body
    assert len(body["components"]) == 5
    assert "Risk signal" in body["explanation"]


@pytest.mark.asyncio
async def test_get_missing_job_posting_returns_not_found(client: AsyncClient) -> None:
    """Unknown posting ids should return HTTP 404."""
    response = await client.get("/api/v1/job-postings/999/risk-score")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_posting_returns_posting_metadata(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Job posting endpoint should return posting metadata."""
    company = Company(name="Metadata Corp")
    db_session.add(company)
    await db_session.flush()

    now = datetime.now(tz=UTC)
    posting = JobPosting(
        company_id=company.id,
        title="Platform Engineer",
        posting_url="https://example.com/jobs/platform-engineer",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(posting)
    await db_session.commit()

    response = await client.get(f"/api/v1/job-postings/{posting.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Platform Engineer"
