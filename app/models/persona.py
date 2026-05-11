import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PersonaStatus(str, enum.Enum):
    """Persona creation status."""

    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class VoiceProfileStatus(str, enum.Enum):
    """Voice cloning profile generation status."""

    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class Persona(BaseModel):
    """Target-based AI persona profile."""

    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True, unique=True)
    status = Column(Enum(PersonaStatus), default=PersonaStatus.PENDING, nullable=False)

    persona_name = Column(String(255), nullable=True)
    personality_summary = Column(Text, nullable=True)
    speaking_style = Column(Text, nullable=True)
    memory_summary = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    values_beliefs = Column(Text, nullable=True)
    memorable_episodes = Column(Text, nullable=True)

    is_voice_profile_created = Column(Boolean, default=False)
    is_consent_required = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    disabled_at = Column(DateTime, nullable=True)
    disabled_reason = Column(String(255), nullable=True)

    target = relationship("Target", back_populates="persona")
    voice_profile = relationship(
        "PersonaVoiceProfile",
        back_populates="persona",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chats = relationship("PersonaChat", back_populates="persona", cascade="all, delete-orphan")


class PersonaVoiceProfile(BaseModel):
    """Voice profile metadata for a persona."""

    __tablename__ = "persona_voice_profiles"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True, unique=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)

    provider = Column(String(100), nullable=False, default="mock")
    model_name = Column(String(255), nullable=True)
    status = Column(Enum(VoiceProfileStatus), default=VoiceProfileStatus.PENDING, nullable=False, index=True)
    reference_audio_count = Column(Integer, default=0, nullable=False)
    reference_audio_total_seconds = Column(Float, nullable=True)
    voice_profile_path = Column(String(512), nullable=True)
    sample_audio_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)

    # Legacy fields retained for API/backward compatibility.
    reference_voice_file_path = Column(String(512), nullable=True)
    reference_voice_mime_type = Column(String(100), nullable=True)
    reference_voice_duration = Column(Integer, nullable=True)

    voice_provider = Column(String(100), nullable=True)
    voice_id = Column(String(255), nullable=True)
    voice_name = Column(String(100), nullable=True)
    profile_metadata = Column("metadata", JSON, nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)

    persona = relationship("Persona", back_populates="voice_profile")
    target = relationship("Target")
