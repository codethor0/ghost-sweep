"""Authentication service layer."""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.exceptions import ConflictError, UnauthorizedError
from app.models.user import User
from app.redis_client import close_redis_client, get_redis_client
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token, decode_token


async def register_user(session: AsyncSession, payload: RegisterRequest) -> User:
    """Create a new user account.

    Args:
        session: Database session.
        payload: Registration payload.

    Returns:
        User: Newly created user.

    Raises:
        ConflictError: When email or username already exists.
    """
    existing = await session.execute(
        select(User).where(or_(User.email == payload.email, User.username == payload.username))
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Account already exists")

    user = User(
        email=payload.email.lower(),
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def login_user(
    session: AsyncSession,
    settings: Settings,
    payload: LoginRequest,
) -> tuple[TokenResponse, str]:
    """Authenticate a user and issue tokens.

    Args:
        session: Database session.
        settings: Application settings.
        payload: Login payload.

    Returns:
        tuple[TokenResponse, str]: Access token response and refresh token.

    Raises:
        UnauthorizedError: When credentials are invalid.
    """
    identifier = payload.identifier.lower()
    result = await session.execute(
        select(User).where(
            or_(User.email == identifier, User.username == identifier),
            User.is_active.is_(True),
        )
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError()

    access_token = create_access_token(settings, str(user.id))
    refresh_token, token_id = create_refresh_token(settings, str(user.id))

    redis = await get_redis_client(settings)
    try:
        await redis.setex(
            f"refresh:{token_id}",
            settings.refresh_token_expire_days * 86400,
            str(user.id),
        )
    finally:
        await close_redis_client(redis)

    return TokenResponse(access_token=access_token), refresh_token


async def refresh_access_token(
    settings: Settings,
    refresh_token: str,
) -> TokenResponse:
    """Exchange a refresh token for a new access token.

    Args:
        settings: Application settings.
        refresh_token: Refresh token supplied by client.

    Returns:
        TokenResponse: New access token response.

    Raises:
        UnauthorizedError: When the refresh token is invalid or revoked.
    """
    try:
        payload = decode_token(settings, refresh_token)
    except Exception as exc:
        raise UnauthorizedError() from exc

    if payload.get("type") != "refresh":
        raise UnauthorizedError()

    token_id = payload.get("jti")
    subject = payload.get("sub")
    if token_id is None or subject is None:
        raise UnauthorizedError()

    redis = await get_redis_client(settings)
    try:
        stored_subject = await redis.get(f"refresh:{token_id}")
    finally:
        await close_redis_client(redis)

    if stored_subject != subject:
        raise UnauthorizedError()

    return TokenResponse(access_token=create_access_token(settings, subject))
