import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.models.base import Base, BaseModel


class MessageType(str, enum.Enum):
    """Persona chat message type."""

    TEXT = "TEXT"
    AUDIO = "AUDIO"


class SenderType(str, enum.Enum):
    """Persona chat message sender."""

    USER = "USER"
    PERSONA = "PERSONA"
    SYSTEM = "SYSTEM"


class PersonaChat(BaseModel):
    """Chat session with a persona."""

    __tablename__ = "persona_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="persona_chats")
    persona = relationship("Persona", back_populates="chats")
    messages = relationship("PersonaMessage", back_populates="chat", cascade="all, delete-orphan")


class PersonaMessage(Base):
    """Message in a persona chat."""

    __tablename__ = "persona_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("persona_chats.id"), nullable=False, index=True)
    sender_type = Column(Enum(SenderType), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=True)
    audio_file_path = Column(String(512), nullable=True)
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    hidden_at = Column(DateTime, nullable=True)
    hidden_reason = Column(String(255), nullable=True)

    chat = relationship("PersonaChat", back_populates="messages")
