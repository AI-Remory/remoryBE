from datetime import datetime
from typing import Optional

from pydantic import BaseModel

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
    file_path: str
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    taken_at: Optional[datetime]
    location: Optional[str]
    ai_caption: Optional[str]
    emotion_keywords: Optional[list[str]]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True


class PhotoMemoryDeleteResponse(BaseModel):
    message: str = "Photo memory deleted successfully"
