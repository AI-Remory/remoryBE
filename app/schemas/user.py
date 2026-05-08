from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import TimestampMixin


class UserBase(BaseModel):
    """사용자 기본 정보"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserSignUp(UserBase):
    """회원가입 요청"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class UserResponse(UserBase, TimestampMixin):
    """사용자 응답"""
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class LoginResponse(BaseModel):
    """로그인 응답"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

