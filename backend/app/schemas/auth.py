"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    """Payload for user login."""

    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)


class TokenResponse(BaseModel):
    """Access token returned to API clients."""

    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Payload for refresh token exchange."""

    refresh_token: str
