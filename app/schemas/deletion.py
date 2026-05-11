from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.deletion import DeletionStatus, DeletionTargetType
from app.schemas.common import TimestampMixin


class DeletionRequestCreateRequest(BaseModel):
    target_type: DeletionTargetType
    target_id: int | None = None
    reason: Optional[str] = None


class DeletionRequestResponse(TimestampMixin):
    id: int
    user_id: int
    target_type: DeletionTargetType
    target_id: int | None
    reason: Optional[str]
    status: DeletionStatus
    requested_at: datetime
    processed_at: Optional[datetime]
    processed_by: int | None
    admin_note: Optional[str]
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)
