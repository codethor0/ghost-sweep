"""Company endpoint tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


@pytest.mark.asyncio
async def test_list_companies_returns_paginated_results(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Company list endpoint should paginate existing records."""
    db_session.add(Company(name="Alpha Corp"))
    db_session.add(Company(name="Beta Corp"))
    await db_session.commit()

    response = await client.get("/api/v1/companies?page=1&page_size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_create_company_requires_authentication(client: AsyncClient) -> None:
    """Creating a company should require a bearer token."""
    response = await client.post(
        "/api/v1/companies",
        json={"name": "Gamma Corp", "website": "https://gamma.example"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_company_with_authentication_persists_record(client: AsyncClient) -> None:
    """Authenticated users should be able to create company profiles."""
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "employer@example.com",
            "username": "employer1",
            "password": "StrongPass123!",
        },
    )
    token = register.json()["access_token"]

    response = await client.post(
        "/api/v1/companies",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Delta Corp", "website": "https://delta.example"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Delta Corp"
