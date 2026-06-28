"""Refresh token service and auth refresh flow tests."""

import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import Settings, get_settings
from app.dependencies import get_settings_dependency
from app.main import app
from app.redis_client import RedisClient
from app.services.refresh_tokens import (
    hash_refresh_token,
    issue_refresh_token,
    refresh_token_key,
    revoke_refresh_token,
    validate_refresh_token,
)

DEFAULT_PASSWORD = "StrongPass123!"


def _register_payload() -> dict[str, str]:
    """Build a unique registration payload."""
    suffix = uuid4().hex[:8]
    return {
        "email": f"user-{suffix}@example.com",
        "username": f"user_{suffix}",
        "password": DEFAULT_PASSWORD,
    }


@pytest.mark.asyncio
async def test_issue_refresh_token_stores_hash_with_ttl(redis_client: RedisClient) -> None:
    """Issuing a refresh token should store only the SHA-256 hash with TTL."""
    settings = get_settings()
    user_id = uuid4()
    token = await issue_refresh_token(redis_client, user_id, settings)

    token_hash = hash_refresh_token(token)
    stored_user_id = await redis_client.get(refresh_token_key(token_hash))
    ttl = await redis_client.ttl(refresh_token_key(token_hash))

    assert stored_user_id == str(user_id)
    assert ttl > 0
    assert ttl <= settings.refresh_token_expire_days * 86400
    assert token_hash != token


@pytest.mark.asyncio
async def test_validate_refresh_token_returns_user_id(redis_client: RedisClient) -> None:
    """Valid refresh tokens should resolve to the issuing user."""
    settings = get_settings()
    user_id = uuid4()
    token = await issue_refresh_token(redis_client, user_id, settings)

    assert await validate_refresh_token(redis_client, token) == user_id


@pytest.mark.asyncio
async def test_validate_missing_refresh_token_returns_none(redis_client: RedisClient) -> None:
    """Unknown refresh tokens should not resolve to a user."""
    assert await validate_refresh_token(redis_client, "missing-token") is None


@pytest.mark.asyncio
async def test_validate_expired_refresh_token_returns_none(redis_client: RedisClient) -> None:
    """Expired refresh tokens should not resolve to a user."""
    settings = Settings(refresh_token_expire_days=1)
    user_id = uuid4()
    token = await issue_refresh_token(redis_client, user_id, settings)
    token_hash = hash_refresh_token(token)
    await redis_client.expire(refresh_token_key(token_hash), 1)
    await asyncio.sleep(1.1)

    assert await validate_refresh_token(redis_client, token) is None


@pytest.mark.asyncio
async def test_revoke_refresh_token_deletes_key(redis_client: RedisClient) -> None:
    """Revoking a refresh token should delete its Redis entry."""
    settings = get_settings()
    user_id = uuid4()
    token = await issue_refresh_token(redis_client, user_id, settings)

    await revoke_refresh_token(redis_client, token)

    assert await validate_refresh_token(redis_client, token) is None


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(client: AsyncClient) -> None:
    """Valid refresh requests should return a new access token."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200
    body = register_response.json()
    original_access_token = body["access_token"]
    refresh_token = body["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["refresh_token"] == refresh_token
    assert refreshed["access_token"]
    assert refreshed["access_token"] != original_access_token


@pytest.mark.asyncio
async def test_refresh_rejects_missing_token(client: AsyncClient) -> None:
    """Missing refresh tokens should return 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "missing-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    """Logout should delete the refresh token from Redis."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200
    refresh_token = register_response.json()["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_remains_valid_after_logout(client: AsyncClient) -> None:
    """Logout should revoke refresh tokens without invalidating access tokens."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200
    body = register_response.json()
    access_token = body["access_token"]
    refresh_token = body["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 204

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200


@pytest.mark.asyncio
async def test_auth_rate_limit_returns_429(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auth routes should return 429 after the configured threshold."""
    limited_settings = get_settings().model_copy(update={"auth_rate_limit_per_minute": 2})

    async def override_get_settings() -> Settings:
        return limited_settings

    app.dependency_overrides[get_settings_dependency] = override_get_settings

    try:
        login_payload = {"identifier": "missing-user@example.com", "password": DEFAULT_PASSWORD}
        first = await client.post("/api/v1/auth/login", json=login_payload)
        second = await client.post("/api/v1/auth/login", json=login_payload)
        third = await client.post("/api/v1/auth/login", json=login_payload)

        assert first.status_code == 401
        assert second.status_code == 401
        assert third.status_code == 429
        assert third.json()["detail"] == "Too many requests"
    finally:
        app.dependency_overrides.pop(get_settings_dependency, None)


@pytest.mark.asyncio
async def test_logout_is_not_rate_limited(client: AsyncClient) -> None:
    """Logout should not be subject to auth rate limiting."""
    payload = _register_payload()
    register_response = await client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 200
    refresh_token = register_response.json()["refresh_token"]

    for _ in range(3):
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_response.status_code == 204
        refresh_token = (
            await client.post(
                "/api/v1/auth/login",
                json={"identifier": payload["email"], "password": DEFAULT_PASSWORD},
            )
        ).json()["refresh_token"]
