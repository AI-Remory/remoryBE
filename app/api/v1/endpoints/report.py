"""Report API endpoints for users and admins."""

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_admin_user, get_current_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.report import (
    CreateReportRequest,
    ReportResponse,
    AdminReportResponse,
    UpdateReportStatusRequest,
    AdminReportListResponse,
)
from app.services.report_service import report_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
async def create_report(
    request_data: CreateReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new report.

    User can report inappropriate content like personas, storybooks, messages, etc.
    """
    try:
        return report_service.create_report(db, current_user.id, request_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=PaginatedResponse[ReportResponse])
async def list_user_reports(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List reports created by the current user."""
    try:
        result = report_service.get_user_reports(db, current_user.id, page, size)
        return PaginatedResponse(
            total=result["total"],
            skip=(page - 1) * size,
            limit=size,
            items=result["items"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_user_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific report created by the current user."""
    try:
        return report_service.get_user_report(db, current_user.id, report_id)
    except RemoryException as e:
        raise to_http_exception(e)

