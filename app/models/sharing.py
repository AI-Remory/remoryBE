from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
import secrets
from app.models.base import BaseModel


class SharePermission(str, enum.Enum):
    """공유 권한"""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


class ShareLink(BaseModel):
    """개인 전달 공유 링크"""
    __tablename__ = "share_links"

    id = Column(Integer, primary_key=True, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    share_token = Column(String(64), unique=True, nullable=False, index=True, default=lambda: secrets.token_urlsafe(48))
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW, nullable=False)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    is_expired = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    storybook = relationship("StoryBook", back_populates="share_links")


class MemoryGroup(BaseModel):
    """그룹 공유 공간"""
    __tablename__ = "memory_groups"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    group_code = Column(String(20), unique=True, nullable=False, index=True)
    invite_link_token = Column(String(64), unique=True, nullable=True)
    profile_image_path = Column(String(512), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    creator = relationship("User", back_populates="memory_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    storybooks = relationship("GroupStoryBook", back_populates="group", cascade="all, delete-orphan")


class GroupMember(BaseModel):
    """그룹 멤버"""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("memory_groups.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    group = relationship("MemoryGroup", back_populates="members")


class GroupStoryBook(BaseModel):
    """그룹과 스토리북의 관계"""
    __tablename__ = "group_storybooks"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("memory_groups.id"), nullable=False, index=True)
    storybook_id = Column(Integer, ForeignKey("storybooks.id"), nullable=False, index=True)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    group = relationship("MemoryGroup", back_populates="storybooks")
    storybook = relationship("StoryBook", back_populates="group_stories")

