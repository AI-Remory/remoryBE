"""Admin APIs."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_admin_user
from app.models.audit_log import AuditAction, AuditTargetType
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.schemas.deletion import DeletionRequestResponse
from app.schemas.target_verification import (
    VerificationRequestAdminResponse,
    VerificationRequestApproveRequest,
    VerificationRequestNeedMoreInfoRequest,
    VerificationRequestRejectRequest,
    VerificationRequestRevokeRequest,
)
from app.schemas.usage_limit import (
    UsageLimitResponse,
    PersonaUsageLimitResponse,
    RateLimitEventResponse,
    UpdateUsageLimitRequest,
    UpdatePersonaUsageLimitRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.deletion_service import deletion_service
from app.services.rate_limit_service import RateLimitService
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


@router.get(
    "/deletion-requests",
    response_model=list[DeletionRequestResponse],
)
async def list_deletion_requests(
    status: str | None = Query(default=None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all deletion requests (admin only)."""
    try:
        status_filter = None
        if status is not None:
            try:
                from app.models.deletion import DeletionStatus
                status_filter = DeletionStatus(status)
            except (KeyError, ValueError) as exc:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid status value",
                ) from exc
        return deletion_service.list_deletion_requests_admin(db, status_filter)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get(
    "/deletion-requests/{request_id}",
    response_model=DeletionRequestResponse,
)
async def get_deletion_request(
    request_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Get a deletion request detail (admin only)."""
    try:
        return deletion_service.get_deletion_request_admin(db, request_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/deletion-requests/{request_id}/approve-and-process",
    response_model=DeletionRequestResponse,
)
async def approve_and_process_deletion_request(
    request_id: int,
    admin_note: str | None = Query(default=None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin approves and immediately processes a deletion request."""
    try:
        return deletion_service.process_deletion_request(
            db,
            admin_user.id,
            request_id,
            admin_note=admin_note,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch(
    "/deletion-requests/{request_id}/reject",
    response_model=DeletionRequestResponse,
)
async def reject_deletion_request(
    request_id: int,
    admin_note: str | None = Query(default=None),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin rejects a deletion request."""
    try:
        return deletion_service.reject_deletion_request(
            db,
            admin_user.id,
            request_id,
            admin_note=admin_note,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    action: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: int | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List audit logs (admin only).

    Query parameters:
    - action: AuditAction enum value
    - actor_user_id: Filter by user who performed action
    - target_type: AuditTargetType enum value
    - target_id: Filter by target ID
    - start_date: ISO format datetime (e.g., 2026-05-12T10:00:00)
    - end_date: ISO format datetime (e.g., 2026-05-12T20:00:00)
    - page: Page number (1-indexed)
    - size: Page size (1-100)
    """
    try:
        # Parse action enum
        parsed_action = None
        if action:
            try:
                parsed_action = AuditAction[action]
            except KeyError:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid action value: {action}",
                )

        # Parse target_type enum
        parsed_target_type = None
        if target_type:
            try:
                parsed_target_type = AuditTargetType[target_type]
            except KeyError:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid target_type value: {target_type}",
                )

        result = AuditLogService.list_audit_logs(
            db,
            page=page,
            size=size,
            action=parsed_action,
            actor_user_id=actor_user_id,
            target_type=parsed_target_type,
            target_id=target_id,
            start_date=start_date,
            end_date=end_date,
        )

        return PaginatedResponse(
            total=result["total"],
            skip=(page - 1) * size,
            limit=size,
            items=result["items"],
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/usage-limits", response_model=PaginatedResponse[UsageLimitResponse])
async def list_usage_limits(
    user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List user usage limits (admin only)."""
    try:
        result = RateLimitService.list_user_usage_limits(
            db,
            skip=(page - 1) * size,
            limit=size,
        )

        # Build response with remaining counts
        items_response = []
        for item in result["items"]:
            items_response.append({
                "id": item.id,
                "user_id": item.user_id,
                "period_ym": item.period_ym,
                "voice_generation_count": item.voice_generation_count,
                "voice_generation_limit": item.voice_generation_limit,
                "voice_generation_remaining": item.voice_generation_limit - item.voice_generation_count,
                "stt_request_count": item.stt_request_count,
                "stt_request_limit": item.stt_request_limit,
                "stt_request_remaining": item.stt_request_limit - item.stt_request_count,
                "voice_call_seconds": item.voice_call_seconds,
                "voice_call_seconds_limit": item.voice_call_seconds_limit,
                "voice_call_seconds_remaining": item.voice_call_seconds_limit - item.voice_call_seconds,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            })

        return PaginatedResponse(
            total=result["total"],
            skip=(page - 1) * size,
            limit=size,
            items=items_response,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.patch("/users/{user_id}/usage-limit", response_model=UsageLimitResponse)
async def update_user_usage_limit(
    user_id: int,
    update_data: UpdateUsageLimitRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update user usage limit (admin only)."""
    try:
        usage_limit = RateLimitService.update_user_usage_limit(
            db,
            user_id,
            voice_generation_limit=update_data.voice_generation_limit,
            stt_request_limit=update_data.stt_request_limit,
            voice_call_seconds_limit=update_data.voice_call_seconds_limit,
        )

        return {
            "id": usage_limit.id,
            "user_id": usage_limit.user_id,
            "period_ym": usage_limit.period_ym,
            "voice_generation_count": usage_limit.voice_generation_count,
            "voice_generation_limit": usage_limit.voice_generation_limit,
            "voice_generation_remaining": usage_limit.voice_generation_limit - usage_limit.voice_generation_count,
            "stt_request_count": usage_limit.stt_request_count,
            "stt_request_limit": usage_limit.stt_request_limit,
            "stt_request_remaining": usage_limit.stt_request_limit - usage_limit.stt_request_count,
            "voice_call_seconds": usage_limit.voice_call_seconds,
            "voice_call_seconds_limit": usage_limit.voice_call_seconds_limit,
            "voice_call_seconds_remaining": usage_limit.voice_call_seconds_limit - usage_limit.voice_call_seconds,
            "created_at": usage_limit.created_at,
            "updated_at": usage_limit.updated_at,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.patch("/personas/{persona_id}/usage-limit", response_model=PersonaUsageLimitResponse)
async def update_persona_usage_limit(
    persona_id: int,
    update_data: UpdatePersonaUsageLimitRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update persona usage limit (admin only)."""
    try:
        usage_limit = RateLimitService.update_persona_usage_limit(
            db,
            persona_id,
            voice_generation_limit=update_data.voice_generation_limit,
            voice_call_seconds_limit=update_data.voice_call_seconds_limit,
        )

        return {
            "id": usage_limit.id,
            "persona_id": usage_limit.persona_id,
            "period_ym": usage_limit.period_ym,
            "voice_generation_count": usage_limit.voice_generation_count,
            "voice_generation_limit": usage_limit.voice_generation_limit,
            "voice_generation_remaining": usage_limit.voice_generation_limit - usage_limit.voice_generation_count,
            "voice_call_seconds": usage_limit.voice_call_seconds,
            "voice_call_seconds_limit": usage_limit.voice_call_seconds_limit,
            "voice_call_seconds_remaining": usage_limit.voice_call_seconds_limit - usage_limit.voice_call_seconds,
            "created_at": usage_limit.created_at,
            "updated_at": usage_limit.updated_at,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/rate-limit-events", response_model=PaginatedResponse[RateLimitEventResponse])
async def list_rate_limit_events(
    user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List rate limit events (admin only)."""
    try:
        result = RateLimitService.list_rate_limit_events(
            db,
            user_id=user_id,
            skip=(page - 1) * size,
            limit=size,
        )

        return PaginatedResponse(
            total=result["total"],
            skip=(page - 1) * size,
            limit=size,
            items=result["items"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
