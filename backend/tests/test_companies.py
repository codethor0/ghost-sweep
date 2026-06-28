"""Company read API tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


@pytest.mark.asyncio
async def test_list_companies_returns_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_company: Company,
) -> None:
    """Company list should return paginated results."""
    second = Company(
        name=f"Second Corp {uuid4().hex[:8]}",
        locations=["Austin"],
    )
    db_session.add(second)
    await db_session.flush()

    response = await client.get("/api/v1/companies?page=1&page_size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_get_company_returns_detail(client: AsyncClient, sample_company: Company) -> None:
    """Company detail should return the requested company."""
    response = await client.get(f"/api/v1/companies/{sample_company.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(sample_company.id)
    assert body["name"] == sample_company.name


@pytest.mark.asyncio
async def test_get_company_returns_404_for_missing_id(client: AsyncClient) -> None:
    """Unknown companies should return 404."""
    response = await client.get(f"/api/v1/companies/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_company_integrity_score_returns_breakdown(
    client: AsyncClient,
    sample_company: Company,
) -> None:
    """Company integrity score should include score and breakdown."""
    response = await client.get(f"/api/v1/companies/{sample_company.id}/integrity-score")
    assert response.status_code == 200
    body = response.json()
    assert 0.0 <= body["score"] <= 100.0
    assert isinstance(body["breakdown"], dict)
    assert body["breakdown"]
