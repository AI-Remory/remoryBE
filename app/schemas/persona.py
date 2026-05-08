from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.persona import PersonaStatus


class PersonaCreateRequest(BaseModel):
    """Persona 생성 요청"""
    target_id: int
    personality_summary: Optional[str] = None
    speaking_style: Optional[str] = None
    values_beliefs: Optional[str] = None
    memorable_episodes: Optional[str] = None


class PersonaUpdateRequest(BaseModel):
    """Persona 수정 요청"""
    personality_summary: Optional[str] = None
    speaking_style: Optional[str] = None
    values_beliefs: Optional[str] = None
    memorable_episodes: Optional[str] = None


class PersonaVoiceProfileResponse(TimestampMixin):
    """Persona 음성 프로필 응답"""
    id: int
    persona_id: int
    reference_voice_file_path: Optional[str]
    reference_voice_mime_type: Optional[str]
    voice_provider: Optional[str]
    voice_id: Optional[str]
    voice_name: Optional[str]

    class Config:
        from_attributes = True


class PersonaResponse(TimestampMixin):
    """Persona 응답"""
    id: int
    target_id: int
    status: PersonaStatus
    personality_summary: Optional[str]
    speaking_style: Optional[str]
    values_beliefs: Optional[str]
    memorable_episodes: Optional[str]
    is_voice_profile_created: bool
    is_consent_required: bool

    class Config:
        from_attributes = True


class PersonaDetailResponse(PersonaResponse):
    """Persona 상세 응답"""
    voice_profile: Optional[PersonaVoiceProfileResponse]

