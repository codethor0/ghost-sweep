"""Authentication endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_with_duplicate_email_returns_conflict(client: AsyncClient) -> None:
    """Duplicate registration attempts should return HTTP 409."""
    payload = {
        "email": "seeker@example.com",
        "username": "jobseeker1",
        "password": "StrongPass123!",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "seeker@example.com",
            "username": "jobseeker2",
            "password": "StrongPass123!",
        },
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_login_with_invalid_credentials_returns_unauthorized(client: AsyncClient) -> None:
    """Invalid login credentials should not reveal account existence details."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "missing@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
