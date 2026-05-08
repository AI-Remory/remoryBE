from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class StoryBook(BaseModel):
    """생성된 스토리북"""
    __tablename__ = "storybooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_path = Column(String(512), nullable=True)

    is_published = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    user = relationship("User", back_populates="storybooks")
    target = relationship("Target", foreign_keys=[target_id])
    chapters = relationship("StoryChapter", back_populates="storybook", cascade="all, delete-orphan")
    voice_narrations = relationship("StoryVoiceNarration", back_populates="storybook", cascade="all, delete-orphan")
    share_links = relationship("ShareLink", back_populates="storybook", cascade="all, delete-orphan")
    group_stories = relationship("GroupStoryBook", back_populates="storybook", cascade="all, delete-orphan")


class StoryChapter(BaseModel):
    """스토리북 챕터/문단"""
    __tablename__ = "story_chapters"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    chapter_order = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    storybook = relationship("StoryBook", back_populates="chapters")
    voice_narrations = relationship("StoryVoiceNarration", back_populates="chapter", cascade="all, delete-orphan")


class StoryVoiceNarration(BaseModel):
    """스토리북 음성 내레이션"""
    __tablename__ = "story_voice_narrations"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("story_chapters.id"), nullable=True, index=True)

    # 음성 파일 정보
    narration_file_path = Column(String(512), nullable=False)
    narration_mime_type = Column(String(100), nullable=False)
    narration_duration_seconds = Column(Integer, nullable=True)

    # 음성 타입
    narration_type = Column(String(50), nullable=False)  # "original" (원본 음성) 또는 "tts" (생성 음성)

    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    storybook = relationship("StoryBook", back_populates="voice_narrations")
    chapter = relationship("StoryChapter", back_populates="voice_narrations")

