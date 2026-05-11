"""관리자 API"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_admin_user
from app.models.user import User
from app.schemas.target_verification import (
    VerificationRequestAdminResponse,
    VerificationRequestApproveRequest,
    VerificationRequestRejectRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.verification_service import verification_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/verification-requests",
    response_model=PaginatedResponse[VerificationRequestAdminResponse],
)
async def list_pending_verification_requests(
    skip: int = 0,
    limit: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """미검토 입증 요청 목록 조회"""
    try:
        result = verification_service.get_pending_verification_requests(
            db,
            skip,
            limit,
        )

        return PaginatedResponse(
            total=result["total"],
            skip=skip,
            limit=limit,
            items=result["items"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/verification-requests/{request_id}/approve",
    response_model=VerificationRequestAdminResponse,
)
async def approve_verification_request(
    request_id: int,
    _: VerificationRequestApproveRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """입증 요청 승인"""
    try:
        request = verification_service.approve_verification_request(
            db,
            request_id,
            admin_user.id,
        )

        return request
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/verification-requests/{request_id}/reject",
    response_model=VerificationRequestAdminResponse,
)
async def reject_verification_request(
    request_id: int,
    reject_data: VerificationRequestRejectRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """입증 요청 거절"""
    try:
        request = verification_service.reject_verification_request(
            db,
            request_id,
            admin_user.id,
            reject_data.rejection_reason,
        )

        return request
    except RemoryException as e:
        raise to_http_exception(e)


