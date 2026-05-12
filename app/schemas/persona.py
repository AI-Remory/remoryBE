from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.persona import PersonaStatus, VoiceProfileStatus, VoiceProfileReviewStatus
from app.schemas.common import TimestampMixin


class PersonaCreateRequest(BaseModel):
    """Request body reserved for future persona generation options."""

    pass


class PersonaStatusResponse(BaseModel):
    persona_id: int
    target_id: int
    status: PersonaStatus

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class PersonaVoiceProfileResponse(TimestampMixin):
    id: int
    persona_id: int
    target_id: Optional[int] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    status: Optional[VoiceProfileStatus] = None
    review_status: Optional[VoiceProfileReviewStatus] = None
    reference_audio_count: Optional[int] = None
    reference_audio_total_seconds: Optional[float] = None
    reference_audio_paths_json: Optional[list[str]] = None
    total_reference_duration_ms: Optional[int] = None
    voice_profile_path: Optional[str] = None
    sample_audio_path: Optional[str] = None
    quality_score: Optional[float] = None
    similarity_score: Optional[float] = None
    noise_score: Optional[float] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    error_message: Optional[str] = None
    reference_voice_file_path: Optional[str]
    reference_voice_mime_type: Optional[str]
    reference_voice_duration: Optional[int]
    voice_provider: Optional[str]
    voice_id: Optional[str]
    voice_name: Optional[str]
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="profile_metadata")

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


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


class VoiceProfileReviewRequest(BaseModel):
    review_note: Optional[str] = None


