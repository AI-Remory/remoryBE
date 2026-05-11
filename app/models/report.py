"""Report model for handling user reports of inappropriate content."""

import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ReportTargetType(str, enum.Enum):
    """Types of objects that can be reported."""
    PERSONA = "PERSONA"
    PERSONA_CHAT = "PERSONA_CHAT"
    PERSONA_MESSAGE = "PERSONA_MESSAGE"
    STORYBOOK = "STORYBOOK"
    SHARE_LINK = "SHARE_LINK"
    TARGET = "TARGET"
    USER = "USER"


class ReportReasonType(str, enum.Enum):
    """Reasons for reporting content."""
    UNAUTHORIZED_VOICE_USE = "UNAUTHORIZED_VOICE_USE"
    PRIVACY_VIOLATION = "PRIVACY_VIOLATION"
    HARMFUL_CONTENT = "HARMFUL_CONTENT"
    IMPERSONATION = "IMPERSONATION"
    COPYRIGHT_OR_RIGHTS = "COPYRIGHT_OR_RIGHTS"
    SPAM = "SPAM"
    OTHER = "OTHER"


class ReportStatus(str, enum.Enum):
    """Status of a report."""
    PENDING = "PENDING"
    REVIEWING = "REVIEWING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"
    ACTION_TAKEN = "ACTION_TAKEN"


class Report(BaseModel):
    """User report for inappropriate content."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_type = Column(Enum(ReportTargetType), nullable=False, index=True)
    target_id = Column(Integer, nullable=False, index=True)
    reason_type = Column(Enum(ReportReasonType), nullable=False)
    reason_detail = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False, index=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    admin_note = Column(Text, nullable=True)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

