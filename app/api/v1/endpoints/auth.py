"""인증 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
    MessageResponse,
    AuthResponse,
    TokenResponse,
    UserResponse,
)
from app.services.user_service import user_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    """회원가입"""
    try:
        user = user_service.create_user(db, user_data)
        tokens = user_service.create_token_pair_for_user(db, user)
        return AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    except RemoryException as e:
        raise to_http_exception(e)


# Backward compatibility for existing clients
@router.post("/sign-up", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up_alias(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    return await register(user_data, db)


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    """로그인"""
    try:
        user = user_service.authenticate_user(db, credentials.email, credentials.password)
        tokens = user_service.create_token_pair_for_user(db, user)
        return AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 조회"""
    return UserResponse.model_validate(current_user)


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """리프레시 토큰으로 access/refresh 토큰 재발급"""
    try:
        tokens = user_service.refresh_access_token(db, request.refresh_token)
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
        )
    except RemoryException as e:
        raise to_http_exception(e)
    except HTTPException:
        raise


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    """리프레시 토큰 폐기 (로그아웃)"""
    try:
        user_service.revoke_refresh_token(db, request.refresh_token)
        return MessageResponse(message="Logged out successfully")
    except RemoryException as e:
        raise to_http_exception(e)
    except HTTPException:
        raise
