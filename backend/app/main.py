"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.config import get_settings
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return basic service health metadata."""
    return HealthResponse(status="ok", service=settings.app_name)


@app.get("/")
async def root() -> dict[str, str]:
    """Return API metadata."""
    return {"service": settings.app_name, "status": "ok", "api_prefix": settings.api_prefix}
