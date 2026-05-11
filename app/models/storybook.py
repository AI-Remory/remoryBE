import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class StoryBookSourceType(str, enum.Enum):
    """Source used to generate a storybook."""

    INTERVIEW = "INTERVIEW"
    PHOTO_MEMORY = "PHOTO_MEMORY"
    SELF_STORY = "SELF_STORY"


class StoryBookStatus(str, enum.Enum):
    """Storybook generation status."""

    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    FAILED = "FAILED"


class StoryBookVisibility(str, enum.Enum):
    """Storybook visibility policy."""

    PRIVATE = "PRIVATE"
    LINK = "LINK"
    GROUP = "GROUP"
    PUBLIC = "PUBLIC"


class StoryBook(BaseModel):
    """Generated interactive storybook."""

    __tablename__ = "storybooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    photo_memory_id = Column(Integer, ForeignKey("photo_memories.id"), nullable=True, index=True)
    interview_session_id = Column(Integer, ForeignKey("ai_interview_sessions.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    source_type = Column(Enum(StoryBookSourceType), nullable=False)
    status = Column(Enum(StoryBookStatus), default=StoryBookStatus.DRAFT, nullable=False)
    visibility = Column(Enum(StoryBookVisibility), default=StoryBookVisibility.PRIVATE, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    disabled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="storybooks")
    photo_memory = relationship("PhotoMemory")
    interview_session = relationship("AIInterviewSession")
    chapters = relationship(
        "StoryChapter",
        back_populates="storybook",
        cascade="all, delete-orphan",
        order_by="StoryChapter.order_index",
    )
    voice_narrations = relationship("StoryVoiceNarration", back_populates="storybook", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="storybook", cascade="all, delete-orphan")
    group_stories = relationship("GroupStoryBook", back_populates="storybook", cascade="all, delete-orphan")


class StoryChapter(BaseModel):
    """Chapter in a storybook."""

    __tablename__ = "story_chapters"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    storybook = relationship("StoryBook", back_populates="chapters")
    voice_narrations = relationship("StoryVoiceNarration", back_populates="chapter", cascade="all, delete-orphan")


class StoryVoiceNarration(BaseModel):
    """Storybook voice narration."""

    __tablename__ = "story_voice_narrations"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("story_chapters.id"), nullable=True, index=True)
    narration_file_path = Column(String(512), nullable=False)
    narration_mime_type = Column(String(100), nullable=False)
    narration_duration_seconds = Column(Integer, nullable=True)
    narration_type = Column(String(50), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    storybook = relationship("StoryBook", back_populates="voice_narrations")
    chapter = relationship("StoryChapter", back_populates="voice_narrations")
