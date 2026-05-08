from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class PersonaStatus(str, enum.Enum):
    """페르소나 상태"""
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"


class Persona(BaseModel):
    """Target 기반 가상 페르소나"""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True, unique=True)
    status = Column(Enum(PersonaStatus), default=PersonaStatus.CREATING, nullable=False)

    # 페르소나 프로필
    personality_summary = Column(Text, nullable=True)
    speaking_style = Column(Text, nullable=True)  # 말투
    values_beliefs = Column(Text, nullable=True)  # 가치관
    memorable_episodes = Column(Text, nullable=True)  # 기억할만한 에피소드

    is_voice_profile_created = Column(Boolean, default=False)
    is_consent_required = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    target = relationship("Target", back_populates="persona")
    voice_profile = relationship(
        "PersonaVoiceProfile",
        back_populates="persona",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chats = relationship("PersonaChat", back_populates="persona", cascade="all, delete-orphan")


class PersonaVoiceProfile(BaseModel):
    """음성 대화/내레이션용 음성 프로필"""
    __tablename__ = "persona_voice_profiles"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False, index=True, unique=True)
    reference_voice_file_path = Column(String(512), nullable=True)
    reference_voice_mime_type = Column(String(100), nullable=True)
    reference_voice_duration = Column(Integer, nullable=True)

    # 음성 프로필 메타데이터 (TTS/Voice API 연동용)
    voice_provider = Column(String(100), nullable=True)  # openai, google, etc
    voice_id = Column(String(255), nullable=True)  # 외부 API 음성 ID
    voice_name = Column(String(100), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    persona = relationship("Persona", back_populates="voice_profile")

