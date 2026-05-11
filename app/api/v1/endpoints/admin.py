"""Admin APIs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_admin_user
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.target_verification import (
    VerificationRequestAdminResponse,
    VerificationRequestApproveRequest,
    VerificationRequestNeedMoreInfoRequest,
    VerificationRequestRejectRequest,
    VerificationRequestRevokeRequest,
)
from app.services.verification_service import verification_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/verification-requests",
    response_model=PaginatedResponse[VerificationRequestAdminResponse],
)
async def list_verification_requests(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        status_filter = None
        if status is not None:
            try:
                status_filter = verification_service._parse_status(status)
            except (KeyError, ValueError) as exc:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid status value",
                ) from exc

        result = verification_service.get_admin_verification_requests(db, status_filter, page, size)
        return PaginatedResponse(
            total=result["total"],
            skip=(page - 1) * size,
            limit=size,
            items=result["items"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get(
    "/verification-requests/{request_id}",
    response_model=VerificationRequestAdminResponse,
)
async def get_admin_verification_request(
    request_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        return verification_service.get_verification_request(db, request_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/verification-requests/{request_id}/file")
async def get_admin_verification_file(
    request_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        request = verification_service.get_verification_request(db, request_id)
        path = verification_service.resolve_submitted_file_path(request)
        return FileResponse(
            path,
            media_type=request.mime_type,
            filename=request.original_filename,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/verification-requests/{request_id}/approve",
    response_model=VerificationRequestAdminResponse,
)
async def approve_verification_request(
    request_id: int,
    approve_data: VerificationRequestApproveRequest | None = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        approve_data = approve_data or VerificationRequestApproveRequest()
        return verification_service.approve_verification_request(
            db,
            request_id,
            admin_user.id,
            admin_note=approve_data.admin_note,
            expires_at=approve_data.expires_at,
        )
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
    try:
        return verification_service.reject_verification_request(
            db,
            request_id,
            admin_user.id,
            reject_data.rejection_reason,
            admin_note=reject_data.admin_note,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/verification-requests/{request_id}/need-more-info",
    response_model=VerificationRequestAdminResponse,
)
async def need_more_info_verification_request(
    request_id: int,
    need_more_info_data: VerificationRequestNeedMoreInfoRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        return verification_service.need_more_info_verification_request(
            db,
            request_id,
            admin_user.id,
            need_more_info_data.admin_note,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/verification-requests/{request_id}/revoke",
    response_model=VerificationRequestAdminResponse,
)
async def revoke_verification_request(
    request_id: int,
    revoke_data: VerificationRequestRevokeRequest | None = None,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    try:
        revoke_data = revoke_data or VerificationRequestRevokeRequest()
        return verification_service.revoke_verification_request(
            db,
            request_id,
            admin_user.id,
            admin_note=revoke_data.admin_note,
        )
    except RemoryException as e:
        raise to_http_exception(e)
