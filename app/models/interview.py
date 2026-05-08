from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class InterviewType(str, enum.Enum):
    """인터뷰 타입"""
    TARGET_PROFILE = "target_profile"  # Target 프로필 보완 질문
    PHOTO_MEMORY = "photo_memory"  # 사진 기반 질문
    PERSONA_CREATION = "persona_creation"  # 페르소나 생성 기본 질문


class PhotoMemory(BaseModel):
    """사진 기반 스토리북 생성용 사진 기억"""
    __tablename__ = "photo_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    photo_file_path = Column(String(512), nullable=False)
    photo_mime_type = Column(String(100), nullable=False)
    photo_original_filename = Column(String(512), nullable=False)
    photo_description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    interview_sessions = relationship(
        "AIInterviewSession",
        back_populates="photo_memory",
    )


class AIInterviewSession(BaseModel):
    """AI 인터뷰 세션 (질문-답변)"""
    __tablename__ = "ai_interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)
    photo_memory_id = Column(Integer, ForeignKey("photo_memories.id"), nullable=True, index=True)
    interview_type = Column(Enum(InterviewType), nullable=False)

    current_question = Column(Text, nullable=True)
    user_answer = Column(Text, nullable=True)
    follow_up_question = Column(Text, nullable=True)  # 꼬리 질문

    is_completed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    user = relationship("User", back_populates="interview_sessions")
    target = relationship("Target", foreign_keys=[target_id])
    photo_memory = relationship("PhotoMemory", back_populates="interview_sessions")

