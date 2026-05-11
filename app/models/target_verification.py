import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VerificationType(str, enum.Enum):
    """Target relationship verification document type."""

    FAMILY_RELATION_CERTIFICATE = "FAMILY_RELATION_CERTIFICATE"
    ID_CARD = "ID_CARD"
    SELF_DECLARATION = "SELF_DECLARATION"
    OTHER = "OTHER"


class VerificationStatus(str, enum.Enum):
    """Target verification workflow status."""

    PENDING = "PENDING"
    NEED_MORE_INFO = "NEED_MORE_INFO"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class TargetVerificationRequest(BaseModel):
    """Relationship verification request for a target."""

    __tablename__ = "target_verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    verification_type = Column(Enum(VerificationType), nullable=False)
    status = Column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    submitted_file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    applicant_note = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="verification_requests", foreign_keys=[user_id])
    target = relationship("Target", back_populates="verification_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
