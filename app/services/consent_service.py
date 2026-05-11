from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.consent import ConsentLog, ConsentType
from app.services.target_service import target_service
from app.utils.exceptions import ForbiddenException, ValidationException


class ConsentService:

    @staticmethod
    def _consent_query(
        user_id: int,
        consent_type: ConsentType,
        target_id: Optional[int],
    ):
        conditions = [
            ConsentLog.user_id == user_id,
            ConsentLog.consent_type == consent_type,
        ]
        if target_id is None:
            conditions.append(ConsentLog.target_id.is_(None))
        else:
            conditions.append(ConsentLog.target_id == target_id)
        return select(ConsentLog).where(*conditions).order_by(ConsentLog.created_at.desc(), ConsentLog.id.desc())

    @staticmethod
    def create_consent(
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
        is_consented: bool,
        details: Optional[str] = None,
    ) -> ConsentLog:
        """동의 저장"""
        if target_id is None and consent_type != ConsentType.STORYBOOK_SHARE:
            raise ValidationException("target_id is required for this consent type")

        if target_id is not None:
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
            .order_by(ConsentLog.created_at.desc(), ConsentLog.id.desc())
        ).scalars().all()

    @staticmethod
    def check_consent(
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
    ) -> None:
        """동의 여부 확인 — 최신 기록이 미동의이거나 없으면 403"""
        latest_consent = db.execute(
            ConsentService._consent_query(user_id, consent_type, target_id).limit(1)
        ).scalars().first()

        if not latest_consent or not latest_consent.is_consented:
            raise ForbiddenException(f"{consent_type.value} 동의가 필요합니다.")


consent_service = ConsentService()
