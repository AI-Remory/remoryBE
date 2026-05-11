from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.target import TargetType
from app.schemas.common import TimestampMixin


class TargetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: TargetType = TargetType.OTHER


class TargetUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_type: Optional[TargetType] = None


class TargetResponse(TimestampMixin):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    target_type: TargetType
    profile_image_path: Optional[str]
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class TargetDetailResponse(TargetResponse):
    media_count: int = 0
    has_persona: bool = False
