from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    """사용자 역할"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """서비스 사용자 계정"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)

    # 관계
    targets = relationship("Target", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    uploaded_media = relationship("TargetMedia", back_populates="uploader", cascade="all, delete-orphan")
    photo_memories = relationship("PhotoMemory", back_populates="user", cascade="all, delete-orphan")
    persona_chats = relationship("PersonaChat", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("AIInterviewSession", back_populates="user", cascade="all, delete-orphan")
    storybooks = relationship("StoryBook", back_populates="user", cascade="all, delete-orphan")
    memory_groups = relationship("MemoryGroup", back_populates="owner", cascade="all, delete-orphan")
    consent_logs = relationship("ConsentLog", back_populates="user", cascade="all, delete-orphan")
    verification_requests = relationship(
        "TargetVerificationRequest",
        back_populates="user",
        foreign_keys="TargetVerificationRequest.user_id",
        cascade="all, delete-orphan",
    )
    reports = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_user_id", cascade="all, delete-orphan")
