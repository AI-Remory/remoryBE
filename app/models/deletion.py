from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class DeletionItemType(str, enum.Enum):
    """삭제 항목 타입"""
    PHOTO = "photo"
    VOICE = "voice"
    MESSAGE = "message"
    STORYBOOK = "storybook"
    PERSONA = "persona"
    CHAT = "chat"


class DeletionStatus(str, enum.Enum):
    """삭제 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DeletionRequest(BaseModel):
    """데이터 삭제 요청"""
    __tablename__ = "deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_type = Column(Enum(DeletionItemType), nullable=False)
    item_id = Column(Integer, nullable=False)
    status = Column(Enum(DeletionStatus), default=DeletionStatus.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    file_paths = Column(String(2048), nullable=True)  # 삭제할 파일 경로들 (JSON)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    user = relationship("User", back_populates="deletion_requests")

