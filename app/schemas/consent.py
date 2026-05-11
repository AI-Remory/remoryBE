from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.consent import ConsentType
from app.schemas.common import TimestampMixin


class ConsentCreate(BaseModel):
    target_id: Optional[int] = None
    consent_type: ConsentType
    consent_version: str = "v1"
    consent_text_snapshot: Optional[str] = None
    is_agreed: Optional[bool] = None
    is_consented: Optional[bool] = None
    details: Optional[str] = None

    @model_validator(mode="after")
    def ensure_agreement_value(self):
        if self.is_agreed is None and self.is_consented is None:
            self.is_agreed = True
        elif self.is_agreed is None:
            self.is_agreed = self.is_consented
        elif self.is_consented is None:
            self.is_consented = self.is_agreed
        return self


class ConsentResponse(TimestampMixin):
    id: int
    user_id: int
    target_id: Optional[int]
    consent_type: ConsentType
    consent_version: str
    consent_text_snapshot: Optional[str]
    is_agreed: bool
    agreed_at: Optional[datetime]
    revoked_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_consented: bool
    details: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class ConsentRevokeResponse(ConsentResponse):
    pass


# Backward-compatible schema names.
ConsentLogCreateRequest = ConsentCreate
ConsentLogResponse = ConsentResponse
