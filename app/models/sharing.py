import enum
import secrets

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SharePermission(str, enum.Enum):
    """Group sharing permission placeholder."""

    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


class ShareLink(BaseModel):
    """Token-based personal share link for a storybook."""

    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(128), unique=True, nullable=False, index=True, default=lambda: secrets.token_urlsafe(48))
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    disabled_at = Column(DateTime, nullable=True)

    storybook = relationship("StoryBook", back_populates="share_links")


class MemoryGroup(BaseModel):
    """Group sharing space."""

    __tablename__ = "memory_groups"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    group_code = Column(String(20), unique=True, nullable=False, index=True)
    invite_link_token = Column(String(64), unique=True, nullable=True)
    profile_image_path = Column(String(512), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)

    creator = relationship("User", back_populates="memory_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    storybooks = relationship("GroupStoryBook", back_populates="group", cascade="all, delete-orphan")


class GroupMember(BaseModel):
    """Group member."""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("memory_groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    group = relationship("MemoryGroup", back_populates="members")


class GroupStoryBook(BaseModel):
    """Association between a group and a storybook."""

    __tablename__ = "group_storybooks"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("memory_groups.id"), nullable=False, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)

    group = relationship("MemoryGroup", back_populates="storybooks")
    storybook = relationship("StoryBook", back_populates="group_stories")
