"""Schemas for report operations."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.report import ReportTargetType, ReportReasonType, ReportStatus
from app.schemas.common import TimestampMixin


class CreateReportRequest(BaseModel):
    """Create report request."""

    target_type: ReportTargetType
    target_id: int
    reason_type: ReportReasonType
    reason_detail: Optional[str] = None


class ReportResponse(TimestampMixin):
    """Report response model."""

    id: int
    reporter_user_id: int
    target_type: ReportTargetType
    target_id: int
    reason_type: ReportReasonType
    reason_detail: Optional[str] = None
    status: ReportStatus
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminReportResponse(TimestampMixin):
    """Admin report response model with reporter info."""

    id: int
    reporter_user_id: int
    reporter_email: Optional[str] = None
    reporter_nickname: Optional[str] = None
    target_type: ReportTargetType
    target_id: int
    reason_type: ReportReasonType
    reason_detail: Optional[str] = None
    status: ReportStatus
    reviewed_by: Optional[int] = None
    reviewed_by_email: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    admin_note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateReportStatusRequest(BaseModel):
    """Update report status request."""

    admin_note: Optional[str] = None


class ReportListResponse(BaseModel):
    """Report list response."""

    total: int
    skip: int
    limit: int
    items: list[ReportResponse]

    model_config = ConfigDict(from_attributes=True)


class AdminReportListResponse(BaseModel):
    """Admin report list response."""

    total: int
    skip: int
    limit: int
    items: list[AdminReportResponse]

    model_config = ConfigDict(from_attributes=True)

