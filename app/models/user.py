from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    """사용자 계정"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    targets = relationship("Target", back_populates="user", cascade="all, delete-orphan")
    persona_chats = relationship("PersonaChat", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("AIInterviewSession", back_populates="user", cascade="all, delete-orphan")
    storybooks = relationship("StoryBook", back_populates="user", cascade="all, delete-orphan")
    memory_groups = relationship("MemoryGroup", back_populates="creator", cascade="all, delete-orphan")
    consent_logs = relationship("ConsentLog", back_populates="user", cascade="all, delete-orphan")
    deletion_requests = relationship("DeletionRequest", back_populates="user", cascade="all, delete-orphan")

