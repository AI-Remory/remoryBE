import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class VoiceCallSessionStatus(str, enum.Enum):
    """Voice call websocket session status."""

    CONNECTED = "CONNECTED"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    FAILED = "FAILED"


class VoiceCallSession(BaseModel):
    """Realtime voice call session metadata."""

    __tablename__ = "voice_call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    chat_id = Column(Integer, ForeignKey("persona_chats.id"), nullable=True, index=True)
    status = Column(
        Enum(VoiceCallSessionStatus),
        default=VoiceCallSessionStatus.CONNECTED,
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    total_duration_seconds = Column(Integer, default=0, nullable=False)
    error_message = Column(String(512), nullable=True)

    user = relationship("User")
    persona = relationship("Persona")
    chat = relationship("PersonaChat")

