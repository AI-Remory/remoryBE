"""사용자 계정 서비스"""
from datetime import timedelta, datetime, UTC
import hashlib
import secrets
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.models.auth import RefreshToken
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.settings import settings
from app.utils.exceptions import NotFoundException, ValidationException, UnauthorizedException
from app.schemas.user import RegisterRequest


class UserService:
    """사용자 계정 관리"""

    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def create_user(db: Session, user_data: RegisterRequest) -> User:
        """회원가입"""
        existing_email = db.execute(
            select(User).where(User.email == user_data.email)
        ).scalar_one_or_none()
        if existing_email:
            raise ValidationException("Email already registered")

        existing_nickname = db.execute(
            select(User).where(User.nickname == user_data.nickname)
        ).scalar_one_or_none()
        if existing_nickname:
            raise ValidationException("Nickname already taken")

        user = User(
            email=user_data.email,
            nickname=user_data.nickname,
            password_hash=hash_password(user_data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """로그인 인증"""
        user = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        return user

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _issue_refresh_token(db: Session, user_id: int) -> str:
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expires_at = UserService._utcnow_naive() + refresh_token_expires
        jti = secrets.token_hex(16)

        refresh_token = create_refresh_token(
            data={"sub": str(user_id), "jti": jti},
            expires_delta=refresh_token_expires,
        )

        token_row = RefreshToken(
            user_id=user_id,
            jti=jti,
            token_hash=UserService._hash_token(refresh_token),
            expires_at=expires_at,
        )
        db.add(token_row)
        return refresh_token

    @staticmethod
    def create_token_pair_for_user(db: Session, user: User) -> dict[str, str]:
        """사용자용 access/refresh 토큰 발급"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )
        refresh_token = UserService._issue_refresh_token(db, user.id)
        db.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> dict[str, str]:
        """리프레시 토큰으로 토큰 재발급"""
        payload = verify_token(refresh_token, expected_type="refresh")
        raw_sub = payload.get("sub")
        jti = payload.get("jti")

        if raw_sub is None or jti is None:
            raise UnauthorizedException("Invalid refresh token")

        try:
            user_id = int(raw_sub)
        except (TypeError, ValueError):
            raise UnauthorizedException("Invalid refresh token")

        stored_token = db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).scalar_one_or_none()

        if not stored_token or stored_token.user_id != user_id:
            raise UnauthorizedException("Refresh token not recognized")

        if stored_token.is_revoked:
            raise UnauthorizedException("Refresh token already revoked")

        if stored_token.expires_at <= UserService._utcnow_naive():
            stored_token.is_revoked = True
            stored_token.revoked_at = UserService._utcnow_naive()
            db.commit()
            raise UnauthorizedException("Refresh token expired")

        if stored_token.token_hash != UserService._hash_token(refresh_token):
            stored_token.is_revoked = True
            stored_token.revoked_at = UserService._utcnow_naive()
            db.commit()
            raise UnauthorizedException("Invalid refresh token")

        # Rotation: 사용된 refresh 토큰은 즉시 폐기
        stored_token.is_revoked = True
        stored_token.revoked_at = UserService._utcnow_naive()

        user = UserService.get_user_by_id(db, user_id)
        return UserService.create_token_pair_for_user(db, user)

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token: str) -> None:
        """로그아웃 시 refresh 토큰 폐기"""
        payload = verify_token(refresh_token, expected_type="refresh")
        jti = payload.get("jti")
        if jti is None:
            raise UnauthorizedException("Invalid refresh token")

        stored_token = db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        ).scalar_one_or_none()

        if not stored_token:
            raise UnauthorizedException("Refresh token not recognized")

        if stored_token.token_hash != UserService._hash_token(refresh_token):
            stored_token.is_revoked = True
            stored_token.revoked_at = UserService._utcnow_naive()
            db.commit()
            raise UnauthorizedException("Invalid refresh token")

        stored_token.is_revoked = True
        stored_token.revoked_at = UserService._utcnow_naive()
        db.commit()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """ID로 사용자 조회"""
        user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not user:
            raise NotFoundException("User", user_id)

        return user


user_service = UserService()
