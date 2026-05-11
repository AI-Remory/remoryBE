import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ConsentType(str, enum.Enum):
    """Consent categories supported by the service."""

    TARGET_PROFILE_CONSENT = "target_profile_consent"
    PHOTO_UPLOAD_CONSENT = "photo_upload_consent"
    VOICE_UPLOAD_CONSENT = "voice_upload_consent"
    VOICE_CLONING_CONSENT = "voice_cloning_consent"
    AI_PERSONA_CREATION_CONSENT = "ai_persona_creation_consent"
    AI_RESPONSE_NOTICE_CONSENT = "ai_response_notice_consent"
    STORYBOOK_SHARE_CONSENT = "storybook_share_consent"
    GROUP_SHARE_CONSENT = "group_share_consent"
    DATA_RETENTION_CONSENT = "data_retention_consent"
    THIRD_PARTY_AI_PROCESSING_CONSENT = "third_party_ai_processing_consent"

    # Legacy values kept for backward compatibility with existing clients/tests.
    VOICE_COLLECTION = "voice_collection"
    PHOTO_COLLECTION = "photo_collection"
    PERSONA_CREATION = "persona_creation"
    DATA_USAGE = "data_usage"
    AI_PROCESSING = "ai_processing"
    AI_RESPONSE_NOTICE = "ai_response_notice"
    STORYBOOK_SHARE = "storybook_share"


class ConsentLog(BaseModel):
    """Immutable consent history with revocation state."""

    __tablename__ = "consent_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)
    consent_type = Column(Enum(ConsentType), nullable=False)
    consent_version = Column(String(50), nullable=False, default="v1")
    consent_text_snapshot = Column(Text, nullable=True)
    is_agreed = Column(Boolean, nullable=False, default=True)
    agreed_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Legacy fields kept so existing API consumers and fixtures keep working.
    is_consented = Column(Boolean, nullable=False)
    details = Column(String(512), nullable=True)

    user = relationship("User", back_populates="consent_logs")
    target = relationship("Target", back_populates="consent_logs")
