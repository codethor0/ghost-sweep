"""Application root endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint_returns_service_metadata(client: AsyncClient) -> None:
    """Root endpoint should expose basic service metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "ghost-sweep"
    assert body["status"] == "ok"
