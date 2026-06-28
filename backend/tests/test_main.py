"""Application endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_service_status() -> None:
    """Health endpoint should return ok status and service name."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "ghost-sweep"


def test_root_endpoint_returns_api_metadata() -> None:
    """Root endpoint should expose service metadata and API prefix."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "ghost-sweep"
        assert body["status"] == "ok"
        assert body["api_prefix"] == "/api/v1"
