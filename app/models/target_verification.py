from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class VerificationType(str, enum.Enum):
    """검증 문서 유형"""
    FAMILY_RELATION_CERTIFICATE = "family_relation_certificate"
    ID_CARD = "id_card"
    SELF_DECLARATION = "self_declaration"
    OTHER = "other"


class VerificationStatus(str, enum.Enum):
    """검증 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TargetVerificationRequest(BaseModel):
    """대상 관계 입증 요청"""
    __tablename__ = "target_verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    verification_type = Column(
        Enum(VerificationType),
        nullable=False,
    )
    status = Column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    document_file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # 관계
    user = relationship("User", back_populates="verification_requests", foreign_keys=[user_id])
    target = relationship("Target", back_populates="verification_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

