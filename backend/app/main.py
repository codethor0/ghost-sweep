"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.companies import router as companies_router
from app.api.v1.employer_claims import router as employer_claims_router
from app.api.v1.job_postings import router as job_postings_router
from app.api.v1.moderation import router as moderation_router
from app.api.v1.reports import router as reports_router
from app.config import get_settings
from app.redis_client import init_redis_client, shutdown_redis_client
from app.schemas import HealthResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize and tear down shared application resources."""
    await init_redis_client(settings)
    try:
        yield
    finally:
        await shutdown_redis_client()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(companies_router, prefix=settings.api_prefix)
app.include_router(employer_claims_router, prefix=settings.api_prefix)
app.include_router(job_postings_router, prefix=settings.api_prefix)
app.include_router(moderation_router, prefix=settings.api_prefix)
app.include_router(reports_router, prefix=settings.api_prefix)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return basic service health metadata."""
    return HealthResponse(status="ok", service=settings.app_name)


@app.get("/")
async def root() -> dict[str, str]:
    """Return API metadata."""
    return {"service": settings.app_name, "status": "ok", "api_prefix": settings.api_prefix}
