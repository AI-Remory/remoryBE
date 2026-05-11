"""DeletionRequest API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.deletion import DeletionRequestCreateRequest, DeletionRequestResponse
from app.services.deletion_service import deletion_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/deletion-requests", tags=["deletion"])


@router.post("", response_model=DeletionRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_deletion_request(
    request_data: DeletionRequestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create and immediately process a deletion request for current-user data."""
    try:
        return deletion_service.create_deletion_request(db, current_user.id, request_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=list[DeletionRequestResponse])
async def list_deletion_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's deletion requests in newest-first order."""
    try:
        return deletion_service.list_deletion_requests(db, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{request_id}", response_model=DeletionRequestResponse)
async def get_deletion_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get one current-user deletion request."""
    try:
        return deletion_service.get_deletion_request(db, current_user.id, request_id)
    except RemoryException as e:
        raise to_http_exception(e)
