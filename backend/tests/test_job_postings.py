"""Job posting read API tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.job_posting import JobPosting


@pytest.mark.asyncio
async def test_get_job_posting_returns_detail(
    client: AsyncClient,
    sample_job_posting: JobPosting,
) -> None:
    """Job posting detail should return the requested posting."""
    response = await client.get(f"/api/v1/job-postings/{sample_job_posting.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(sample_job_posting.id)
    assert body["title"] == sample_job_posting.title


@pytest.mark.asyncio
async def test_get_job_posting_returns_404_for_missing_id(client: AsyncClient) -> None:
    """Unknown job postings should return 404."""
    response = await client.get(f"/api/v1/job-postings/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_job_posting_risk_score_returns_breakdown(
    client: AsyncClient,
    sample_job_posting: JobPosting,
) -> None:
    """Job posting risk score should include score and breakdown."""
    response = await client.get(f"/api/v1/job-postings/{sample_job_posting.id}/risk-score")
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["score"] <= 100.0
    assert isinstance(body["breakdown"], dict)
    assert body["breakdown"]
