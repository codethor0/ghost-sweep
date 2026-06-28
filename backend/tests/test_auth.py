"""Authentication API and service tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.security.tokens import ACCESS_TOKEN_CLAIM_TYPE

DEFAULT_PASSWORD = "StrongPass123!"


def _register_payload(*, email: str | None = None, username: str | None = None) -> dict[str, str]:
    """Build a unique registration payload."""
    suffix = uuid4().hex[:8]
    return {
        "email": email or f"user-{suffix}@example.com",
        "username": username or f"user_{suffix}",
        "password": DEFAULT_PASSWORD,
    }


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Registration should return a bearer access token."""
    payload = _register_payload()
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert isinstance(body["refresh_token"], str)
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    """Duplicate email registration should return 409."""
    payload = _register_payload()
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = _register_payload(email=payload["email"])
    response = await client.post("/api/v1/auth/register", json=duplicate)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_rejects_duplicate_username(client: AsyncClient) -> None:
    """Duplicate username registration should return 409."""
    payload = _register_payload()
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = _register_payload(username=payload["username"])
    response = await client.post("/api/v1/auth/register", json=duplicate)
    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken"


@pytest.mark.asyncio
async def test_login_with_email(client: AsyncClient) -> None:
    """Login should accept email identifiers."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": payload["email"], "password": DEFAULT_PASSWORD},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_with_username(client: AsyncClient) -> None:
    """Login should accept username identifiers."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": payload["username"], "password": DEFAULT_PASSWORD},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client: AsyncClient) -> None:
    """Invalid passwords should return 401 with a generic message."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": payload["email"], "password": "WrongPass123!"},
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_rejects_unknown_user(client: AsyncClient) -> None:
    """Unknown users should return 401 with a generic message."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "missing-user@example.com", "password": DEFAULT_PASSWORD},
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_me_with_valid_token(client: AsyncClient) -> None:
    """Authenticated requests should return the current user profile."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    body = me_response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    """Missing bearer tokens should return 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(client: AsyncClient) -> None:
    """Invalid bearer tokens should return 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_non_uuid_subject_token(client: AsyncClient) -> None:
    """Valid access tokens with non-UUID subjects should return 401."""
    settings = get_settings()
    assert settings.jwt_secret_key is not None
    payload = {
        "sub": "not-a-uuid",
        "exp": datetime.now(tz=UTC) + timedelta(minutes=15),
        "type": ACCESS_TOKEN_CLAIM_TYPE,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
