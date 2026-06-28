"""Health check routes."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_redis
from app.redis_client import RedisClient, check_redis_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_db_session),
    redis: RedisClient = Depends(get_redis),
) -> HealthResponse:
    """Return service health for database and Redis dependencies.

    Args:
        session: Database session.
        redis: Redis client.

    Returns:
        HealthResponse: Dependency health summary.
    """
    database_status = "unhealthy"
    redis_status = "unhealthy"

    try:
        await session.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"

    try:
        if await check_redis_connection(redis):
            redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    overall = (
        "healthy" if database_status == "healthy" and redis_status == "healthy" else "degraded"
    )
    return HealthResponse(status=overall, database=database_status, redis=redis_status)
