from sqlalchemy import Column, Integer, String, ForeignKey, Enum, BigInteger, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class MediaType(str, enum.Enum):
    """미디어 타입"""
    IMAGE = "image"
    VOICE = "voice"


class TargetMedia(BaseModel):
    """Target의 사진/음성 메타데이터"""
    __tablename__ = "target_media"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    media_type = Column(Enum(MediaType), nullable=False)
    original_filename = Column(String(512), nullable=False)
    stored_filename = Column(String(512), nullable=False)
    file_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    duration_seconds = Column(Integer, nullable=True)  # 음성 파일용
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    target = relationship("Target", back_populates="media")
    uploader = relationship("User", back_populates="uploaded_media")
