"""인증 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserSignUp, UserLogin, LoginResponse, TokenResponse
from app.services.user_service import user_service
from app.utils.exceptions import RemoryException, to_http_exception
from app.core.settings import settings

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/sign-up", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    user_data: UserSignUp,
    db: Session = Depends(get_db),
):
    """회원가입"""
    try:
        user = user_service.create_user(db, user_data)
        access_token = user_service.create_access_token_for_user(user)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """로그인"""
    try:
        user = user_service.authenticate_user(db, credentials.email, credentials.password)
        access_token = user_service.create_access_token_for_user(user)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token():
    """토큰 갱신"""
    # TODO: 나중에 구현
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented yet",
    )

