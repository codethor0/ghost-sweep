"""Authentication API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_current_user, get_db, get_settings_dependency
from app.models.user import User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register_user(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Register a user and return a bearer access token."""
    return await auth_service.register_user(session, settings, payload)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> TokenResponse:
    """Authenticate a user and return a bearer access token."""
    return await auth_service.authenticate_user(session, settings, payload)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user's profile."""
    return current_user
