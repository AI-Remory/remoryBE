from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.consent import ConsentType


class ConsentLogCreateRequest(BaseModel):
    """ConsentLog 생성 요청"""
    target_id: int
    consent_type: ConsentType
    is_consented: bool
    details: Optional[str] = None


class ConsentLogResponse(TimestampMixin):
    """ConsentLog 응답"""
    id: int
    user_id: int
    target_id: Optional[int]
    consent_type: ConsentType
    is_consented: bool
    details: Optional[str]

    class Config:
        from_attributes = True

