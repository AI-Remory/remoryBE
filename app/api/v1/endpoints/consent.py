from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.consent import ConsentLogCreateRequest, ConsentLogResponse
from app.services.consent_service import consent_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["consents"])


@router.post("/consents", response_model=ConsentLogResponse, status_code=status.HTTP_201_CREATED)
def create_consent(
    body: ConsentLogCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.create_consent(
            db=db,
            user_id=current_user.id,
            target_id=body.target_id,
            consent_type=body.consent_type,
            is_consented=body.is_consented,
            details=body.details,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/consents", response_model=List[ConsentLogResponse])
def get_my_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return consent_service.get_user_consents(db=db, user_id=current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)
