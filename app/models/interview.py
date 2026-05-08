import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel


class InterviewType(str, enum.Enum):
    """Supported AI interview session types."""

    TARGET_PROFILE = "TARGET_PROFILE"
    PHOTO_MEMORY = "PHOTO_MEMORY"
    SELF_STORY = "SELF_STORY"


class InterviewStatus(str, enum.Enum):
    """AI interview session status."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PhotoMemory(BaseModel):
    """User-uploaded personal photo memory for storybook creation."""

    __tablename__ = "photo_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(512), nullable=False)
    stored_filename = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    taken_at = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    ai_caption = Column(Text, nullable=True)
    emotion_keywords = Column(JSON, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="photo_memories")
    interview_sessions = relationship(
        "AIInterviewSession",
        back_populates="photo_memory",
    )


class AIInterviewSession(BaseModel):
    """AI interview session."""

    __tablename__ = "ai_interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)
    photo_memory_id = Column(Integer, ForeignKey("photo_memories.id"), nullable=True, index=True)
    session_type = Column(Enum(InterviewType), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(Enum(InterviewStatus), default=InterviewStatus.IN_PROGRESS, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    target = relationship("Target", foreign_keys=[target_id])
    photo_memory = relationship("PhotoMemory", back_populates="interview_sessions")
    questions = relationship(
        "AIInterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AIInterviewQuestion.order_index",
    )


class AIInterviewQuestion(Base):
    """Question generated for an AI interview session."""

    __tablename__ = "ai_interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_interview_sessions.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(100), nullable=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    session = relationship("AIInterviewSession", back_populates="questions")
    answers = relationship(
        "AIInterviewAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AIInterviewAnswer.created_at",
    )


class AIInterviewAnswer(BaseModel):
    """Answer submitted for an AI interview question."""

    __tablename__ = "ai_interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_interview_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("ai_interview_questions.id"), nullable=False, index=True)
    answer_text = Column(Text, nullable=True)
    answer_audio_path = Column(String(512), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    session = relationship("AIInterviewSession")
    question = relationship("AIInterviewQuestion", back_populates="answers")
