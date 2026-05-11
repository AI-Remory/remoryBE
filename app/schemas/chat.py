from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import MessageType, SenderType
from app.schemas.common import TimestampMixin


class PersonaChatCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)


class PersonaChatResponse(TimestampMixin):
    id: int
    user_id: int
    persona_id: int
    title: Optional[str]
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PersonaMessageCreateRequest(BaseModel):
    message_type: MessageType = MessageType.TEXT
    content: Optional[str] = None
    audio_file_path: Optional[str] = None
    generate_audio: bool = False


class PersonaMessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_type: SenderType
    message_type: MessageType
    content: Optional[str]
    audio_file_path: Optional[str]
    is_ai_generated: bool
    created_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PersonaMessagePairResponse(BaseModel):
    user_message: PersonaMessageResponse
    persona_message: PersonaMessageResponse
