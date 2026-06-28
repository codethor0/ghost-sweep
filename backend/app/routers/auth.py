"""Authentication routes."""

from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_db_session
from app.dependencies import enforce_auth_rate_limit, get_settings_dependency
from app.exceptions import UnauthorizedError
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)]
)
async def register(
    payload: RegisterRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Register a new user and return an access token.

    Refresh tokens are returned in an HttpOnly cookie.
    """
    user = await auth_service.register_user(session, payload)
    login_payload = LoginRequest(identifier=user.email, password=payload.password)
    token_response, refresh_token = await auth_service.login_user(session, settings, login_payload)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return token_response


@router.post(
    "/login", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)]
)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Authenticate a user and return an access token."""
    token_response, refresh_token = await auth_service.login_user(session, settings, payload)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return token_response


@router.post(
    "/refresh", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)]
)
async def refresh(
    payload: RefreshRequest | None = None,
    cookie_refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Refresh an access token using a refresh token."""
    token_value = payload.refresh_token if payload is not None else cookie_refresh_token
    if token_value is None:
        raise UnauthorizedError()
    return await auth_service.refresh_access_token(settings, token_value)
