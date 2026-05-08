from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.consent import ConsentLog, ConsentType
from app.services.target_service import target_service
from app.utils.exceptions import ForbiddenException


class ConsentService:

    @staticmethod
    def create_consent(
        db: Session,
        user_id: int,
        target_id: int,
        consent_type: ConsentType,
        is_consented: bool,
        details: str | None = None,
    ) -> ConsentLog:
        """동의 저장"""
        target_service.get_target_by_id(db, target_id, user_id)

        consent = ConsentLog(
            user_id=user_id,
            target_id=target_id,
            consent_type=consent_type,
            is_consented=is_consented,
            details=details,
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def get_user_consents(db: Session, user_id: int) -> list[ConsentLog]:
        """내 동의 내역 전체 조회"""
        return db.execute(
            select(ConsentLog)
            .where(ConsentLog.user_id == user_id)
            .order_by(ConsentLog.created_at.desc())
        ).scalars().all()

    @staticmethod
    def check_consent(
        db: Session,
        user_id: int,
        target_id: int,
        consent_type: ConsentType,
    ) -> None:
        """동의 여부 확인 — 미동의 시 403"""
        result = db.execute(
            select(ConsentLog).where(
                ConsentLog.user_id == user_id,
                ConsentLog.target_id == target_id,
                ConsentLog.consent_type == consent_type,
                ConsentLog.is_consented == True,
            )
        ).scalar_one_or_none()

        if not result:
            raise ForbiddenException(f"{consent_type.value} 동의가 필요합니다.")


consent_service = ConsentService()
