"""Authentication API routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_current_user, get_db, get_redis, get_settings_dependency
from app.models.user import User
from app.redis_client import RedisClient
from app.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services import auth as auth_service
from app.services.rate_limit import check_auth_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    """Return the client IP address for rate limiting.

    Args:
        request: Incoming HTTP request.

    Returns:
        str: Client IP address or a fallback identifier.
    """
    if request.client is None:
        return "unknown"
    return request.client.host


@router.post("/register", response_model=TokenResponse)
async def register_user(
    payload: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Register a user and return bearer access and refresh tokens."""
    await check_auth_rate_limit(redis, "register", _client_ip(request), settings)
    return await auth_service.register_user(session, redis, settings, payload)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Authenticate a user and return bearer access and refresh tokens."""
    await check_auth_rate_limit(redis, "login", _client_ip(request), settings)
    return await auth_service.authenticate_user(session, redis, settings, payload)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    await check_auth_rate_limit(redis, "refresh", _client_ip(request), settings)
    return await auth_service.refresh_user_tokens(session, redis, settings, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_user(
    payload: LogoutRequest,
    redis: RedisClient = Depends(get_redis),
) -> Response:
    """Revoke a refresh token."""
    await auth_service.logout_user(redis, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
