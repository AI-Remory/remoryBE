from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.common import TimestampMixin


class PhotoMemoryCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    taken_at: Optional[datetime] = None
    location: Optional[str] = None


class PhotoMemoryResponse(TimestampMixin):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    file_path: str = Field(description="Deprecated: use image_api_url with Authorization instead.")
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    taken_at: Optional[datetime]
    location: Optional[str]
    ai_caption: Optional[str]
    emotion_keywords: Optional[list[str]]
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def image_api_url(self) -> str:
        return f"/api/v1/photo-memories/{self.id}/image"


class PhotoMemoryDeleteResponse(BaseModel):
    message: str = "Photo memory deleted successfully"
