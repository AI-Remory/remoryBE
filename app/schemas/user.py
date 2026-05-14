from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Literal

from app.schemas.common import TimestampMixin


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token rotation request."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Common message response."""

    message: str


class UserResponse(TimestampMixin):
    """User response."""

    id: int
    email: EmailStr
    nickname: str
    role: Literal["USER", "ADMIN"]

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    """Authentication response."""

    user: UserResponse
