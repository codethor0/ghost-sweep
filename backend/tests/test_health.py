"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_dependency_status(client: AsyncClient) -> None:
    """Health endpoint should report database and Redis status."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "healthy"
    assert body["redis"] == "healthy"
    assert body["status"] in {"healthy", "degraded"}
