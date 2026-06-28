"""Health check schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Service health status."""

    status: str
    database: str
    redis: str
