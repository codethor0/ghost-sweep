"""Authentication service for user registration and login."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db_errors import raise_conflict_from_integrity_error
from app.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.redis_client import RedisClient
from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token
from app.services.refresh_tokens import (
    issue_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
)
from app.services.user_identity import (
    normalize_email,
    normalize_login_identifier,
    normalize_username,
)


async def register_user(
    session: AsyncSession,
    redis: RedisClient,
    settings: Settings,
    payload: RegisterRequest,
) -> TokenResponse:
    """Register a new user and return access and refresh tokens."""
    email = normalize_email(str(payload.email))
    username = normalize_username(payload.username)

    email_result = await session.execute(select(User.id).where(func.lower(User.email) == email))
    if email_result.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered")

    username_result = await session.execute(
        select(User.id).where(func.lower(User.username) == username)
    )
    if username_result.scalar_one_or_none() is not None:
        raise ConflictError("Username already taken")

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)
    await session.refresh(user)

    refresh_token = await issue_refresh_token(redis, user.id, settings)
    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=refresh_token,
    )


async def authenticate_user(
    session: AsyncSession,
    redis: RedisClient,
    settings: Settings,
    payload: LoginRequest,
) -> TokenResponse:
    """Authenticate a user and return access and refresh tokens."""
    identifier = normalize_login_identifier(payload.identifier)
    result = await session.execute(
        select(User).where(
            or_(func.lower(User.email) == identifier, func.lower(User.username) == identifier)
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError()

    refresh_token = await issue_refresh_token(redis, user.id, settings)
    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=refresh_token,
    )


async def refresh_user_tokens(
    session: AsyncSession,
    redis: RedisClient,
    settings: Settings,
    refresh_token: str,
) -> TokenResponse:
    """Exchange a valid refresh token for rotated access and refresh tokens."""
    rotation = await rotate_refresh_token(redis, refresh_token, settings)
    if rotation is None:
        raise UnauthorizedError()

    user_id, new_refresh_token = rotation
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedError()

    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=new_refresh_token,
    )


async def logout_user(redis: RedisClient, refresh_token: str) -> None:
    """Revoke a refresh token without invalidating existing access tokens."""
    await revoke_refresh_token(redis, refresh_token)


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """Load a user by primary key."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
