import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class DeletionTargetType(str, enum.Enum):
    """Supported deletion target types."""

    TARGET = "TARGET"
    TARGET_MEDIA = "TARGET_MEDIA"
    PERSONA = "PERSONA"
    PERSONA_CHAT = "PERSONA_CHAT"
    PERSONA_MESSAGE = "PERSONA_MESSAGE"
    PHOTO_MEMORY = "PHOTO_MEMORY"
    STORYBOOK = "STORYBOOK"
    SHARE_LINK = "SHARE_LINK"
    MEMORY_GROUP = "MEMORY_GROUP"
    ACCOUNT = "ACCOUNT"


class DeletionStatus(str, enum.Enum):
    """Deletion request status."""

    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DeletionRequest(BaseModel):
    """User data deletion request and processing record."""

    __tablename__ = "deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(Enum(DeletionTargetType), nullable=False)
    target_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(DeletionStatus), default=DeletionStatus.REQUESTED, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    user = relationship("User", back_populates="deletion_requests")


# Backward-compatible alias for older imports.
DeletionItemType = DeletionTargetType
