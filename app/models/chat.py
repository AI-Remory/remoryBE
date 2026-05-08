from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class PersonaChat(BaseModel):
    """페르소나와의 대화방"""
    __tablename__ = "persona_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    user = relationship("User", back_populates="persona_chats")
    persona = relationship("Persona", back_populates="chats")
    messages = relationship("PersonaMessage", back_populates="chat", cascade="all, delete-orphan")


class MessageType(str, enum.Enum):
    """메시지 타입"""
    TEXT = "text"
    AUDIO = "audio"


class SenderType(str, enum.Enum):
    """발신자 타입"""
    USER = "user"
    PERSONA = "persona"
    SYSTEM = "system"


class PersonaMessage(BaseModel):
    """페르소나 대화 메시지"""
    __tablename__ = "persona_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("persona_chats.id"), nullable=False, index=True)
    sender_type = Column(Enum(SenderType), nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    content = Column(Text, nullable=True)  # 텍스트 메시지
    audio_file_path = Column(String(512), nullable=True)  # 음성 파일 경로
    audio_mime_type = Column(String(100), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    chat = relationship("PersonaChat", back_populates="messages")

