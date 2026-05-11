from typing import List

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentRevokeResponse
from app.services.consent_service import consent_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["consents"])


@router.post("/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
def create_consent(
    body: ConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.create_consent(
            db=db,
            user_id=current_user.id,
            target_id=body.target_id,
            consent_type=body.consent_type,
            consent_version=body.consent_version,
            consent_text_snapshot=body.consent_text_snapshot,
            is_agreed=bool(body.is_agreed),
            is_consented=body.is_consented,
            details=body.details,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/consents", response_model=List[ConsentResponse])
def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.get_user_consents(db=db, user_id=current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/targets/{target_id}/consents", response_model=List[ConsentResponse])
def get_target_consents(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.get_target_consents(db=db, user_id=current_user.id, target_id=target_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch("/consents/{consent_id}/revoke", response_model=ConsentRevokeResponse)
def revoke_consent(
    consent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.revoke_consent(db=db, user_id=current_user.id, consent_id=consent_id)
    except RemoryException as e:
        raise to_http_exception(e)
