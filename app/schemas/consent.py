from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.consent import ConsentType
from app.schemas.common import TimestampMixin


class ConsentLogCreateRequest(BaseModel):
    target_id: int
    consent_type: ConsentType
    is_consented: bool
    details: Optional[str] = None


class ConsentLogResponse(TimestampMixin):
    id: int
    user_id: int
    target_id: Optional[int]
    consent_type: ConsentType
    is_consented: bool
    details: Optional[str]

    model_config = ConfigDict(from_attributes=True)
