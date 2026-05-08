from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.persona import PersonaStatus
from app.schemas.common import TimestampMixin


class PersonaCreateRequest(BaseModel):
    """Request body reserved for future persona generation options."""

    pass


class PersonaStatusResponse(BaseModel):
    persona_id: int
    target_id: int
    status: PersonaStatus

    model_config = ConfigDict(from_attributes=True)


class PersonaVoiceProfileResponse(TimestampMixin):
    id: int
    persona_id: int
    reference_voice_file_path: Optional[str]
    reference_voice_mime_type: Optional[str]
    reference_voice_duration: Optional[int]
    voice_provider: Optional[str]
    voice_id: Optional[str]
    voice_name: Optional[str]
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="profile_metadata")

    model_config = ConfigDict(from_attributes=True)


class PersonaResponse(TimestampMixin):
    id: int
    target_id: int
    status: PersonaStatus
    persona_name: Optional[str]
    speaking_style: Optional[str]
    personality_summary: Optional[str]
    memory_summary: Optional[str]
    system_prompt: Optional[str]
    is_voice_profile_created: bool
    is_consent_required: bool

    model_config = ConfigDict(from_attributes=True)


class PersonaDetailResponse(PersonaResponse):
    voice_profile: Optional[PersonaVoiceProfileResponse] = None
