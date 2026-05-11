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
    VERIFICATION_REQUEST = "VERIFICATION_REQUEST"
    ACCOUNT = "ACCOUNT"
    VOICE_PROFILE = "VOICE_PROFILE"
    VOICE_CALL_SESSION = "VOICE_CALL_SESSION"


class DeletionStatus(str, enum.Enum):
    """Deletion request status."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DeletionRequest(BaseModel):
    """User data deletion request and processing record."""

    __tablename__ = "deletion_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(Enum(DeletionTargetType), nullable=False)
    target_id = Column(Integer, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(Enum(DeletionStatus), default=DeletionStatus.PENDING, nullable=False)
    requested_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_note = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Explicitly use foreign_keys to specify which User relationship
    # NOTE: We do NOT use back_populates here because there are multiple foreign keys
    # The User model handles the relationship instead
    user = relationship("User", foreign_keys=[user_id])


# Backward-compatible alias for older imports.
DeletionItemType = DeletionTargetType
