"""Target 관리 서비스"""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.target import Target
from app.models.media import TargetMedia
from app.models.persona import Persona
from app.utils.exceptions import NotFoundException, ForbiddenException
from app.schemas.target import TargetCreateRequest, TargetUpdateRequest


class TargetService:
    """Target 관리"""

    @staticmethod
    def create_target(db: Session, user_id: int, target_data: TargetCreateRequest) -> Target:
        """Target 생성"""
        target = Target(
            user_id=user_id,
            name=target_data.name,
            description=target_data.description,
            target_type=target_data.target_type,
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def get_target_by_id(db: Session, target_id: int, user_id: int = None) -> Target:
        """ID로 Target 조회"""
        target = db.execute(
            select(Target).where(Target.id == target_id)
        ).scalar_one_or_none()

        if not target:
            raise NotFoundException("Target", target_id)

        # 권한 확인 (user_id가 제공된 경우)
        if user_id and target.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this target")

        return target

    @staticmethod
    def get_user_targets(db: Session, user_id: int, skip: int = 0, limit: int = 20):
        """사용자의 Target 목록 조회"""
        query = select(Target).where(
            Target.user_id == user_id,
            Target.is_deleted == False,
        ).offset(skip).limit(limit)

        targets = db.execute(query).scalars().all()

        # 총 개수
        total = db.execute(
            select(func.count(Target.id)).where(
                Target.user_id == user_id,
                Target.is_deleted == False,
            )
        ).scalar()

        return {"total": total, "items": targets}

    @staticmethod
    def update_target(
        db: Session,
        target_id: int,
        user_id: int,
        target_data: TargetUpdateRequest,
    ) -> Target:
        """Target 수정"""
        target = TargetService.get_target_by_id(db, target_id, user_id)

        # 수정 가능한 필드 업데이트
        if target_data.name is not None:
            target.name = target_data.name
        if target_data.description is not None:
            target.description = target_data.description
        if target_data.target_type is not None:
            target.target_type = target_data.target_type

        db.commit()
        db.refresh(target)
        return target

    @staticmethod
    def delete_target(db: Session, target_id: int, user_id: int):
        """Target 삭제 (논리 삭제)"""
        target = TargetService.get_target_by_id(db, target_id, user_id)
        target.is_deleted = True
        db.commit()

    @staticmethod
    def get_target_detail(db: Session, target_id: int, user_id: int = None):
        """Target 상세 정보 (관련 데이터 포함)"""
        target = TargetService.get_target_by_id(db, target_id, user_id)

        # 미디어 개수
        media_count = db.execute(
            select(func.count(TargetMedia.id)).where(
                TargetMedia.target_id == target_id,
                TargetMedia.is_deleted == False,
            )
        ).scalar()

        # 페르소나 존재 여부
        persona = db.execute(
            select(Persona).where(Persona.target_id == target_id)
        ).scalar_one_or_none()

        return {
            "target": target,
            "media_count": media_count or 0,
            "has_persona": persona is not None,
        }


target_service = TargetService()

