"""의존성 주입"""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.user_service import user_service
from app.models.user import User


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    """현재 로그인한 사용자 정보 조회 (의존성)"""
    return user_service.get_user_by_id(db, user_id)


async def auth_user(
    user: User = Depends(get_current_user),
) -> User:
    """인증된 사용자 의존성 alias"""
    return user
