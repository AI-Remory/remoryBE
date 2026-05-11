"""Audit log schemas for API requests/responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.audit_log import AuditAction, AuditTargetType


class AuditLogResponse(BaseModel):
    """Audit log response model."""

    id: int
    actor_user_id: Optional[int] = None
    action: AuditAction
    target_type: Optional[AuditTargetType] = None
    target_id: Optional[int] = None
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

