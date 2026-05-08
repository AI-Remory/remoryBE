from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import TimestampMixin


class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """리프레시 토큰 갱신 요청"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """로그아웃 요청"""
    refresh_token: str


class MessageResponse(BaseModel):
    """공통 메시지 응답"""
    message: str


class UserResponse(TimestampMixin):
    """사용자 응답"""
    id: int
    email: EmailStr
    nickname: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenResponse):
    """로그인/회원가입 응답"""
    user: UserResponse

