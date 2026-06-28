"""Authentication service for user registration and login."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token


async def register_user(
    session: AsyncSession,
    settings: Settings,
    payload: RegisterRequest,
) -> TokenResponse:
    """Register a new user and return an access token.

    Args:
        session: Active database session.
        settings: Application settings.
        payload: Registration request payload.

    Returns:
        TokenResponse: Bearer access token response.

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
    await session.commit()
    await session.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id, settings))


async def authenticate_user(
    session: AsyncSession,
    settings: Settings,
    payload: LoginRequest,
) -> TokenResponse:
    """Authenticate a user and return an access token.

    Args:
        session: Active database session.
        settings: Application settings.
        payload: Login request payload.

    Returns:
        TokenResponse: Bearer access token response.

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

    return TokenResponse(access_token=create_access_token(user.id, settings))


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
