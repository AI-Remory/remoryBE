from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class TargetType(str, enum.Enum):
    """Target 타입"""
    PARENT = "parent"
    GRANDPARENT = "grandparent"
    FRIEND = "friend"
    ROMANTIC = "romantic"
    SELF = "self"
    OTHER = "other"


class Target(BaseModel):
    """가상 페르소나 대상"""
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_type = Column(
        Enum(TargetType),
        default=TargetType.OTHER,
        nullable=False,
    )
    profile_image_path = Column(String(512), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 관계
    user = relationship("User", back_populates="targets")
    media = relationship("TargetMedia", back_populates="target", cascade="all, delete-orphan")
    persona = relationship("Persona", back_populates="target", uselist=False, cascade="all, delete-orphan")
    consent_logs = relationship("ConsentLog", back_populates="target", cascade="all, delete-orphan")

