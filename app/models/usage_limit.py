"""Usage limit models for tracking monthly usage."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UsageLimit(BaseModel):
    """Monthly usage limit tracking for users."""

    __tablename__ = "usage_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    period_ym = Column(String(7), nullable=False, index=True)  # Format: "2026-05"

    # Voice generation (TTS, persona reply synthesis)
    voice_generation_count = Column(Integer, default=0)
    voice_generation_limit = Column(Integer, nullable=False)

    # STT requests (speech-to-text)
    stt_request_count = Column(Integer, default=0)
    stt_request_limit = Column(Integer, nullable=False)

    # Voice call duration in seconds
    voice_call_seconds = Column(Integer, default=0)
    voice_call_seconds_limit = Column(Integer, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    # Composite unique index
    __table_args__ = (
        Index("ix_usage_limits_user_ym", "user_id", "period_ym", unique=True),
    )


class PersonaUsageLimit(BaseModel):
    """Monthly usage limit tracking per persona."""

    __tablename__ = "persona_usage_limits"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    period_ym = Column(String(7), nullable=False, index=True)  # Format: "2026-05"

    # Voice generation count
    voice_generation_count = Column(Integer, default=0)
    voice_generation_limit = Column(Integer, nullable=False)

    # Voice call duration
    voice_call_seconds = Column(Integer, default=0)
    voice_call_seconds_limit = Column(Integer, nullable=False)

    # Relationships
    persona = relationship("Persona", foreign_keys=[persona_id])

    # Composite unique index
    __table_args__ = (
        Index("ix_persona_usage_limits_persona_ym", "persona_id", "period_ym", unique=True),
    )


class RateLimitEvent(BaseModel):
    """Rate limit and abuse detection events."""

    __tablename__ = "rate_limit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # e.g., "rate_limit", "invalid_mime", "file_too_large"
    count = Column(Integer, default=1)  # Number of violations in this event
    window_seconds = Column(Integer, nullable=True)  # Time window for this event
    blocked = Column(Boolean, default=False)  # Was the request blocked?
    reason = Column(String(255), nullable=True)  # Reason for blocking


