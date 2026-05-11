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
    # 민감 문서 관련 메타데이터
    # 정책: 실제 파일은 삭제 요청 시 제거하고, 내부 경로 및 저장파일명(stored_filename),
    # MIME 타입 및 파일 크기와 같은 민감 정보를 null 처리한다.
    # 운영/감사용 최소 메타데이터(id, user_id, target_id, verification_type, status,
    # submitted_at, reviewed_at, reviewed_by, rejection_reason, created_at, updated_at, deleted_at)
    # 은 기록으로 남긴다. original_filename(사용자가 업로드한 원래 파일명)은 민감할 수 있으므로
    # 서비스 정책에 따라 삭제하거나 보관할 수 있다. 현재는 운영상 식별을 돕기 위해 유지하되,
    # 필요시 삭제하도록 정책을 변경할 수 있다.
    document_file_path = Column(String(512), nullable=True)
    original_filename = Column(String(255), nullable=False)
    # stored_filename/mime_type/file_size는 삭제 시 민감 정보로 간주하여 NULL 처리 가능하도록 변경
    stored_filename = Column(String(255), nullable=True, unique=True)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    # 관계
    user = relationship("User", back_populates="verification_requests", foreign_keys=[user_id])
    target = relationship("Target", back_populates="verification_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

