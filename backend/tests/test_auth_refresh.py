"""Additional authentication coverage tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_returns_access_token(client: AsyncClient) -> None:
    """Valid credentials should return a bearer access token."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "StrongPass123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "login@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_unauthorized(client: AsyncClient) -> None:
    """Invalid refresh tokens should return HTTP 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401
