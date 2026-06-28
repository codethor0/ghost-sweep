"""Authentication service for user registration and login."""

from uuid import UUID

from sqlalchemy import or_, select
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
    validate_refresh_token,
)


async def register_user(
    session: AsyncSession,
    redis: RedisClient,
    settings: Settings,
    payload: RegisterRequest,
) -> TokenResponse:
    """Register a new user and return access and refresh tokens.

    Args:
        session: Active database session.
        redis: Active Redis client.
        settings: Application settings.
        payload: Registration request payload.

    Returns:
        TokenResponse: Bearer access and refresh token response.

    Raises:
        ConflictError: When the email or username already exists.
    """
    email_result = await session.execute(select(User).where(User.email == payload.email))
    if email_result.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered")

    username_result = await session.execute(select(User).where(User.username == payload.username))
    if username_result.scalar_one_or_none() is not None:
        raise ConflictError("Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
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
    """Authenticate a user and return access and refresh tokens.

    Args:
        session: Active database session.
        redis: Active Redis client.
        settings: Application settings.
        payload: Login request payload.

    Returns:
        TokenResponse: Bearer access and refresh token response.

    Raises:
        UnauthorizedError: When credentials are invalid.
    """
    result = await session.execute(
        select(User).where(
            or_(User.email == payload.identifier, User.username == payload.identifier)
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
    """Exchange a valid refresh token for a new access token.

    Args:
        session: Active database session.
        redis: Active Redis client.
        settings: Application settings.
        refresh_token: Opaque refresh token from the client.

    Returns:
        TokenResponse: New access token and the same refresh token.

    Raises:
        UnauthorizedError: When the refresh token is missing, expired, or revoked.
    """
    user_id = await validate_refresh_token(redis, refresh_token)
    if user_id is None:
        raise UnauthorizedError()

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedError()

    return TokenResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=refresh_token,
    )


async def logout_user(redis: RedisClient, refresh_token: str) -> None:
    """Revoke a refresh token without invalidating existing access tokens.

    Args:
        redis: Active Redis client.
        refresh_token: Opaque refresh token from the client.
    """
    await revoke_refresh_token(redis, refresh_token)


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    """Load a user by primary key.

    Args:
        session: Active database session.
        user_id: User UUID.

    Returns:
        User | None: Matching user when found.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
