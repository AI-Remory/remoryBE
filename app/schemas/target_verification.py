from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.target_verification import VerificationType, VerificationStatus


class VerificationRequestCreateRequest(BaseModel):
    """입증 요청 생성"""
    verification_type: VerificationType = Field(
        ...,
        description="검증 문서 유형"
    )


class VerificationRequestResponse(BaseModel):
    """입증 요청 응답"""
    id: int
    user_id: int
    target_id: int
    verification_type: VerificationType
    status: VerificationStatus
    original_filename: str
    mime_type: str
    file_size: int
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationRequestDetailResponse(VerificationRequestResponse):
    """입증 요청 상세 응답"""
    pass


class VerificationRequestApproveRequest(BaseModel):
    """입증 승인 요청"""
    pass


class VerificationRequestRejectRequest(BaseModel):
    """입증 거절 요청"""
    rejection_reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="거절 사유"
    )


class VerificationRequestAdminResponse(VerificationRequestResponse):
    """관리자용 입증 요청 응답"""
    pass

