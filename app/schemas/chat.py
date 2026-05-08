from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.chat import MessageType, SenderType


class PersonaChatCreateRequest(BaseModel):
    """PersonaChat 생성 요청"""
    persona_id: int
    title: Optional[str] = None
    description: Optional[str] = None


class PersonaChatResponse(TimestampMixin):
    """PersonaChat 응답"""
    id: int
    user_id: int
    persona_id: int
    title: Optional[str]
    description: Optional[str]
    is_deleted: bool

    class Config:
        from_attributes = True


class PersonaMessageRequest(BaseModel):
    """메시지 전송 요청"""
    chat_id: int
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None  # 텍스트 메시지


class PersonaMessageResponse(TimestampMixin):
    """메시지 응답"""
    id: int
    chat_id: int
    sender_type: SenderType
    message_type: MessageType
    content: Optional[str]
    audio_file_path: Optional[str]
    is_deleted: bool

    class Config:
        from_attributes = True

