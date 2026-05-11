from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent import ConsentLog, ConsentType
from app.services.target_service import target_service
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException


class ConsentService:
    GLOBAL_CONSENT_TYPES = {
        ConsentType.STORYBOOK_SHARE_CONSENT,
        ConsentType.GROUP_SHARE_CONSENT,
        ConsentType.DATA_RETENTION_CONSENT,
        ConsentType.THIRD_PARTY_AI_PROCESSING_CONSENT,
        ConsentType.STORYBOOK_SHARE,
        ConsentType.DATA_USAGE,
        ConsentType.AI_PROCESSING,
    }

    LEGACY_FALLBACKS = {
        ConsentType.TARGET_PROFILE_CONSENT: (ConsentType.DATA_USAGE,),
        ConsentType.PHOTO_UPLOAD_CONSENT: (ConsentType.PHOTO_COLLECTION,),
        ConsentType.VOICE_UPLOAD_CONSENT: (ConsentType.VOICE_COLLECTION,),
        ConsentType.VOICE_CLONING_CONSENT: (ConsentType.VOICE_COLLECTION,),
        ConsentType.AI_PERSONA_CREATION_CONSENT: (ConsentType.PERSONA_CREATION,),
        ConsentType.AI_RESPONSE_NOTICE_CONSENT: (ConsentType.AI_RESPONSE_NOTICE, ConsentType.PERSONA_CREATION),
        ConsentType.STORYBOOK_SHARE_CONSENT: (ConsentType.STORYBOOK_SHARE,),
        ConsentType.GROUP_SHARE_CONSENT: (ConsentType.STORYBOOK_SHARE_CONSENT, ConsentType.STORYBOOK_SHARE),
        ConsentType.THIRD_PARTY_AI_PROCESSING_CONSENT: (ConsentType.AI_PROCESSING,),
        ConsentType.DATA_RETENTION_CONSENT: (ConsentType.DATA_USAGE,),
    }

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

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
    def _is_active_agreement(consent: ConsentLog | None) -> bool:
        return bool(
            consent
            and consent.is_agreed
            and consent.is_consented
            and consent.revoked_at is None
        )

    @classmethod
    def _latest_consent(
        cls,
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
    ) -> ConsentLog | None:
        return db.execute(cls._consent_query(user_id, consent_type, target_id).limit(1)).scalars().first()

    @classmethod
    def create_consent(
        cls,
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
        is_agreed: bool,
        consent_version: str = "v1",
        consent_text_snapshot: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_consented: Optional[bool] = None,
    ) -> ConsentLog:
        if is_consented is None:
            is_consented = is_agreed

        if target_id is None and consent_type not in cls.GLOBAL_CONSENT_TYPES:
            raise ValidationException("target_id is required for this consent type")

        if target_id is not None:
            target_service.get_target_by_id(db, target_id, user_id)

        now = cls._now()
        consent = ConsentLog(
            user_id=user_id,
            target_id=target_id,
            consent_type=consent_type,
            consent_version=consent_version or "v1",
            consent_text_snapshot=consent_text_snapshot or details,
            is_agreed=is_agreed,
            is_consented=is_consented,
            agreed_at=now if is_agreed else None,
            revoked_at=None if is_agreed else now,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        db.add(consent)
        db.commit()
        db.refresh(consent)
        return consent

    @staticmethod
    def get_user_consents(db: Session, user_id: int) -> list[ConsentLog]:
        return db.execute(
            select(ConsentLog)
            .where(ConsentLog.user_id == user_id)
            .order_by(ConsentLog.created_at.desc(), ConsentLog.id.desc())
        ).scalars().all()

    @staticmethod
    def get_target_consents(db: Session, user_id: int, target_id: int) -> list[ConsentLog]:
        target_service.get_target_by_id(db, target_id, user_id)
        return db.execute(
            select(ConsentLog)
            .where(ConsentLog.user_id == user_id, ConsentLog.target_id == target_id)
            .order_by(ConsentLog.created_at.desc(), ConsentLog.id.desc())
        ).scalars().all()

    @staticmethod
    def revoke_consent(db: Session, user_id: int, consent_id: int) -> ConsentLog:
        consent = db.execute(
            select(ConsentLog).where(ConsentLog.id == consent_id, ConsentLog.user_id == user_id)
        ).scalar_one_or_none()
        if consent is None:
            raise NotFoundException("ConsentLog", consent_id)

        consent.is_agreed = False
        consent.is_consented = False
        consent.revoked_at = ConsentService._now()
        db.commit()
        db.refresh(consent)
        return consent

    @classmethod
    def has_active_consent(
        cls,
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
    ) -> bool:
        latest = cls._latest_consent(db, user_id, target_id, consent_type)
        if latest is not None:
            return cls._is_active_agreement(latest)

        for fallback_type in cls.LEGACY_FALLBACKS.get(consent_type, ()):
            fallback = cls._latest_consent(db, user_id, target_id, fallback_type)
            if fallback is not None:
                return cls._is_active_agreement(fallback)
        return False

    @classmethod
    def check_consent(
        cls,
        db: Session,
        user_id: int,
        target_id: Optional[int],
        consent_type: ConsentType,
    ) -> None:
        if not cls.has_active_consent(db, user_id, target_id, consent_type):
            raise ForbiddenException(f"{consent_type.value} consent is required")


consent_service = ConsentService()
