"""사용자 계정 서비스"""
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.settings import settings
from app.utils.exceptions import NotFoundException, ValidationException
from app.schemas.user import UserSignUp, UserLogin


class UserService:
    """사용자 계정 관리"""

    @staticmethod
    def create_user(db: Session, user_data: UserSignUp) -> User:
        """사용자 생성"""
        # 이메일 중복 확인
        existing_user = db.execute(
            select(User).where(User.email == user_data.email)
        ).scalar_one_or_none()
        if existing_user:
            raise ValidationException("Email already registered")

        # 사용자명 중복 확인
        existing_user = db.execute(
            select(User).where(User.username == user_data.username)
        ).scalar_one_or_none()
        if existing_user:
            raise ValidationException("Username already taken")

        # 사용자 생성
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """사용자 인증"""
        user = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if not user:
            raise NotFoundException("User", 0)

        if not verify_password(password, user.hashed_password):
            raise ValidationException("Invalid password")

        if not user.is_active:
            raise ValidationException("User account is inactive")

        return user

    @staticmethod
    def create_access_token_for_user(user: User) -> str:
        """사용자를 위한 액세스 토큰 생성"""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        return create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires,
        )

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

