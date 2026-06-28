"""Report endpoint tests."""

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> str:
    """Register a user and return an access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reporter@example.com",
            "username": "reporter1",
            "password": "StrongPass123!",
        },
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return str(access_token)


@pytest.mark.asyncio
async def test_report_submission_without_evidence_returns_validation_error(
    client: AsyncClient,
) -> None:
    """Reports must include at least one evidence item."""
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Example Corp",
            "job_title": "Backend Engineer",
            "posting_url": "https://example.com/jobs/backend-engineer",
            "category": "stale_repost",
            "timeline_description": (
                "This posting has remained open for several months without updates."
            ),
            "evidence": [],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_report_submission_with_evidence_creates_report(client: AsyncClient) -> None:
    """Valid report submissions should persist report and evidence records."""
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "company_name": "Example Corp",
            "job_title": "Backend Engineer",
            "posting_url": "https://example.com/jobs/backend-engineer",
            "category": "stale_repost",
            "timeline_description": (
                "This posting has remained open for several months without updates."
            ),
            "evidence": [
                {
                    "evidence_type": "screenshot",
                    "source_url": "https://example.com/evidence/1",
                    "description": (
                        "Screenshot showing the same posting reposted across multiple months."
                    ),
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "stale_repost"
    assert len(body["evidence_items"]) == 1
