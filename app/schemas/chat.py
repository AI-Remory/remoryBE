from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

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
    audio_file_path: Optional[str] = Field(
        default=None,
        description="Deprecated: use audio_api_url with Authorization instead.",
    )
    is_ai_generated: bool
    created_at: datetime
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def audio_api_url(self) -> Optional[str]:
        if not self.audio_file_path:
            return None
        return f"/api/v1/chats/{self.chat_id}/messages/{self.id}/audio"


class PersonaMessagePairResponse(BaseModel):
    user_message: PersonaMessageResponse
    persona_message: PersonaMessageResponse
