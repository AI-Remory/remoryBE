from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.media import MediaType


class TargetMediaResponse(TimestampMixin):
    """Target Media 응답"""
    id: int
    target_id: int
    media_type: MediaType
    original_filename: str
    file_path: str
    mime_type: str
    file_size: int
    duration_seconds: Optional[int]
    is_deleted: bool

    class Config:
        from_attributes = True


class MediaUploadResponse(BaseModel):
    """파일 업로드 응답"""
    file_id: int
    filename: str
    file_path: str
    media_type: MediaType
    file_size: int
    mime_type: str
    duration_seconds: Optional[int] = None
    message: str = "File uploaded successfully"

