from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.media import MediaType
from app.schemas.common import TimestampMixin


class TargetMediaResponse(TimestampMixin):
    id: int
    target_id: int
    uploaded_by: int
    media_type: MediaType
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size: int
    duration_seconds: Optional[int]
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class MediaUploadResponse(BaseModel):
    file_id: int
    target_id: int
    uploaded_by: int
    original_filename: str
    stored_filename: str
    file_path: str
    media_type: MediaType
    file_size: int
    mime_type: str
    message: str = "File uploaded successfully"


class MediaDeleteResponse(BaseModel):
    message: str = "Media deleted successfully"
