from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class ConsentType(str, enum.Enum):
    """동의 타입"""
    VOICE_COLLECTION = "voice_collection"  # 음성 수집
    PHOTO_COLLECTION = "photo_collection"  # 사진 수집
    PERSONA_CREATION = "persona_creation"  # 페르소나 생성
    DATA_USAGE = "data_usage"  # 데이터 사용
    AI_PROCESSING = "ai_processing"  # AI 처리
    AI_RESPONSE_NOTICE = "ai_response_notice"  # AI 사용 응답 동의 완료
    STORYBOOK_SHARE = "storybook_share" # 스토리북 공유 동의 완료 


class ConsentLog(BaseModel):
    """음성/사진/페르소나 동의 내역"""
    __tablename__ = "consent_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)
    consent_type = Column(Enum(ConsentType), nullable=False)
    is_consented = Column(Boolean, nullable=False)
    details = Column(String(512), nullable=True)

    # 관계
    user = relationship("User", back_populates="consent_logs")
    target = relationship("Target", back_populates="consent_logs")

