from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.media import MediaType
from app.schemas.common import TimestampMixin


class TargetMediaResponse(TimestampMixin):
    id: int
    target_id: int
    uploaded_by: int
    media_type: MediaType
    original_filename: str
    stored_filename: str
    file_path: str = Field(description="Deprecated: use file_api_url with Authorization instead.")
    mime_type: str
    file_size: int
    duration_seconds: Optional[int]
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def file_api_url(self) -> str:
        return f"/api/v1/targets/{self.target_id}/media/{self.id}/file"


class MediaUploadResponse(BaseModel):
    file_id: int
    target_id: int
    uploaded_by: int
    original_filename: str
    stored_filename: str
    file_path: str = Field(description="Deprecated: use file_api_url with Authorization instead.")
    file_api_url: str
    media_type: MediaType
    file_size: int
    mime_type: str
    message: str = "File uploaded successfully"


class MediaDeleteResponse(BaseModel):
    message: str = "Media deleted successfully"
