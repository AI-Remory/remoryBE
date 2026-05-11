"""Audit log model for tracking sensitive operations."""

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    """Audit log action types."""

    # User actions
    USER_SIGNUP = "USER_SIGNUP"

    # Target actions
    TARGET_CREATED = "TARGET_CREATED"
    TARGET_UPDATED = "TARGET_UPDATED"
    TARGET_DELETED = "TARGET_DELETED"

    # Consent actions
    CONSENT_CREATED = "CONSENT_CREATED"
    CONSENT_REVOKED = "CONSENT_REVOKED"

    # Verification actions
    VERIFICATION_SUBMITTED = "VERIFICATION_SUBMITTED"
    VERIFICATION_APPROVED = "VERIFICATION_APPROVED"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
    VERIFICATION_NEED_MORE_INFO = "VERIFICATION_NEED_MORE_INFO"
    VERIFICATION_REVOKED = "VERIFICATION_REVOKED"

    # Persona actions
    PERSONA_CREATED = "PERSONA_CREATED"
    PERSONA_CHAT_CREATED = "PERSONA_CHAT_CREATED"
    PERSONA_MESSAGE_CREATED = "PERSONA_MESSAGE_CREATED"

    # Voice actions
    VOICE_PROFILE_CREATED = "VOICE_PROFILE_CREATED"
    VOICE_PROFILE_REVIEWED = "VOICE_PROFILE_REVIEWED"
    VOICE_SYNTHESIZED = "VOICE_SYNTHESIZED"
    VOICE_CALL_STARTED = "VOICE_CALL_STARTED"
    VOICE_CALL_ENDED = "VOICE_CALL_ENDED"

    # Deletion actions
    DELETION_REQUESTED = "DELETION_REQUESTED"
    DELETION_COMPLETED = "DELETION_COMPLETED"
    DELETION_REJECTED = "DELETION_REJECTED"

    # Report actions
    REPORT_CREATED = "REPORT_CREATED"
    REPORT_RESOLVED = "REPORT_RESOLVED"

    # System actions
    RATE_LIMIT_BLOCKED = "RATE_LIMIT_BLOCKED"
    ABNORMAL_REQUEST_BLOCKED = "ABNORMAL_REQUEST_BLOCKED"


class AuditTargetType(str, enum.Enum):
    """Types of audit log targets."""

    TARGET = "TARGET"
    CONSENT = "CONSENT"
    VERIFICATION_REQUEST = "VERIFICATION_REQUEST"
    PERSONA = "PERSONA"
    PERSONA_CHAT = "PERSONA_CHAT"
    PERSONA_MESSAGE = "PERSONA_MESSAGE"
    VOICE_PROFILE = "VOICE_PROFILE"
    DELETION_REQUEST = "DELETION_REQUEST"
    REPORT = "REPORT"
    USER = "USER"
    SYSTEM = "SYSTEM"


class AuditLog(BaseModel):
    """Audit log for tracking all sensitive operations."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)
    target_type = Column(Enum(AuditTargetType), nullable=True, index=True)
    target_id = Column(Integer, nullable=True, index=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Relationships
    actor = relationship("User", foreign_keys=[actor_user_id])

