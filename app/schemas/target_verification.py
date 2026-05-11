from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.target_verification import VerificationStatus, VerificationType


class VerificationRequestCreateRequest(BaseModel):
    verification_type: VerificationType
    applicant_note: Optional[str] = Field(default=None, max_length=1000)


class VerificationRequestResponse(BaseModel):
    id: int
    user_id: int
    target_id: int
    verification_type: VerificationType
    status: VerificationStatus
    original_filename: str
    mime_type: str
    file_size: int
    applicant_note: Optional[str] = None
    admin_note: Optional[str] = None
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationRequestDetailResponse(VerificationRequestResponse):
    pass


class VerificationRequestApproveRequest(BaseModel):
    admin_note: Optional[str] = Field(default=None, max_length=1000)
    expires_at: Optional[datetime] = None


class VerificationRequestRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=500)
    admin_note: Optional[str] = Field(default=None, max_length=1000)


class VerificationRequestNeedMoreInfoRequest(BaseModel):
    admin_note: str = Field(..., min_length=5, max_length=1000)


class VerificationRequestRevokeRequest(BaseModel):
    admin_note: Optional[str] = Field(default=None, max_length=1000)


class VerificationRequestAdminResponse(VerificationRequestResponse):
    pass
