"""Audit log service for tracking sensitive operations."""

import json
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import AuditLog, AuditAction, AuditTargetType
from app.schemas.common import PaginatedResponse


class AuditLogService:
    """Service for creating and querying audit logs."""

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def create_audit_log(
        db: Session,
        action: AuditAction,
        actor_user_id: Optional[int] = None,
        target_type: Optional[AuditTargetType] = None,
        target_id: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
        request: Optional[Request] = None,
        raise_on_failure: bool = True,
    ) -> Optional[AuditLog]:
        """Create an audit log entry.

        Args:
            db: Database session
            action: The action being audited
            actor_user_id: ID of the user performing the action (None for system actions)
            target_type: Type of object being acted upon
            target_id: ID of the object being acted upon
            description: Human-readable description of the action
            metadata: Additional metadata (will be JSON-encoded). Sensitive fields like
                     passwords, tokens are excluded.
            request: Optional FastAPI Request object to extract IP and user agent
            raise_on_failure: Re-raise DB errors after rollback. Admin/security
                operations should keep this True so audit failure is visible.
                General user workflows that must continue can pass False.

        Returns:
            Created AuditLog object, or None when raise_on_failure is False and
            the audit INSERT fails.
        """
        # Sanitize metadata to remove sensitive fields
        if metadata:
            metadata = AuditLogService._sanitize_metadata(metadata)

        # Extract IP and User-Agent from request
        ip_address = None
        user_agent = None
        if request:
            ip_address = AuditLogService._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")[:512]

        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description,
            metadata_json=json.dumps(metadata) if metadata else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        try:
            db.add(audit_log)
            db.flush()
            db.commit()
            db.refresh(audit_log)
            return audit_log
        except SQLAlchemyError:
            db.rollback()
            if raise_on_failure:
                raise
            return None

    @staticmethod
    def _sanitize_metadata(metadata: dict) -> dict:
        """Remove sensitive fields from metadata before logging.

        Fields that are excluded:
        - password, passwd, pwd
        - token, access_token, refresh_token
        - secret, api_key, secret_key
        - Authorization header
        """
        if not isinstance(metadata, dict):
            return metadata

        sensitive_keys = {
            "password",
            "passwd",
            "pwd",
            "token",
            "access_token",
            "refresh_token",
            "secret",
            "api_key",
            "secret_key",
            "authorization",
        }

        sanitized = {}
        for key, value in metadata.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = AuditLogService._sanitize_metadata(value)
            else:
                sanitized[key] = value

        return sanitized

    @staticmethod
    def _get_client_ip(request: Request) -> Optional[str]:
        """Extract client IP from request, considering proxy headers."""
        # Check X-Forwarded-For header (common with proxies)
        if "x-forwarded-for" in request.headers:
            # Take the first IP if multiple are listed
            return request.headers["x-forwarded-for"].split(",")[0].strip()

        # Check X-Real-IP header
        if "x-real-ip" in request.headers:
            return request.headers["x-real-ip"]

        # Fall back to client connection IP
        return request.client.host if request.client else None

    @staticmethod
    def list_audit_logs(
        db: Session,
        page: int = 1,
        size: int = 20,
        action: Optional[AuditAction] = None,
        actor_user_id: Optional[int] = None,
        target_type: Optional[AuditTargetType] = None,
        target_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """List audit logs with optional filtering.

        Args:
            db: Database session
            page: Page number (1-indexed)
            size: Page size
            action: Filter by action type
            actor_user_id: Filter by actor user ID
            target_type: Filter by target type
            target_id: Filter by target ID
            start_date: Filter logs created after this date
            end_date: Filter logs created before this date

        Returns:
            Dictionary with total count and list of audit logs
        """
        query = select(AuditLog)

        if action:
            query = query.where(AuditLog.action == action)
        if actor_user_id:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if target_type:
            query = query.where(AuditLog.target_type == target_type)
        if target_id:
            query = query.where(AuditLog.target_id == target_id)
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)

        # Get total count
        count_query = select(func.count(AuditLog.id)).select_from(AuditLog)
        if action:
            count_query = count_query.where(AuditLog.action == action)
        if actor_user_id:
            count_query = count_query.where(AuditLog.actor_user_id == actor_user_id)
        if target_type:
            count_query = count_query.where(AuditLog.target_type == target_type)
        if target_id:
            count_query = count_query.where(AuditLog.target_id == target_id)
        if start_date:
            count_query = count_query.where(AuditLog.created_at >= start_date)
        if end_date:
            count_query = count_query.where(AuditLog.created_at <= end_date)

        total = db.execute(count_query).scalar() or 0

        # Apply pagination
        offset = (page - 1) * size
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size)

        items = db.execute(query).scalars().all()

        return {"total": total, "items": items, "page": page, "size": size}

    @staticmethod
    def search_audit_logs(
        db: Session,
        page: int = 1,
        size: int = 20,
        **filters,
    ) -> PaginatedResponse:
        """Search audit logs and return paginated results.

        Args:
            db: Database session
            page: Page number (1-indexed)
            size: Page size
            **filters: Filter parameters (action, actor_user_id, target_type, etc.)

        Returns:
            PaginatedResponse with audit logs
        """
        result = AuditLogService.list_audit_logs(db, page, size, **filters)
        return PaginatedResponse(
            total=result["total"],
            page=result["page"],
            size=result["size"],
            data=result["items"],
        )



