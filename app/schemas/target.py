from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.common import TimestampMixin
from app.models.target import TargetType


class TargetCreateRequest(BaseModel):
    """Target 생성 요청"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: TargetType = TargetType.OTHER


class TargetUpdateRequest(BaseModel):
    """Target 수정 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_type: Optional[TargetType] = None


class TargetResponse(TimestampMixin):
    """Target 응답"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    target_type: TargetType
    profile_image_path: Optional[str]
    is_deleted: bool

    class Config:
        from_attributes = True


class TargetDetailResponse(TargetResponse):
    """Target 상세 응답 (관련 데이터 포함)"""
    media_count: int = 0
    has_persona: bool = False

