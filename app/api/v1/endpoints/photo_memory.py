"""PhotoMemory API."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.photo_memory import (
    PhotoMemoryCreateRequest,
    PhotoMemoryDeleteResponse,
    PhotoMemoryResponse,
)
from app.services.photo_memory_service import photo_memory_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/photo-memories", tags=["photo-memory"])


@router.post("", response_model=PhotoMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_photo_memory(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    taken_at: Optional[datetime] = Form(None),
    location: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a personal photo memory for storybook creation."""
    try:
        return photo_memory_service.create_photo_memory(
            db=db,
            user_id=current_user.id,
            photo_data=PhotoMemoryCreateRequest(
                title=title,
                description=description,
                taken_at=taken_at,
                location=location,
            ),
            upload_file=file,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=list[PhotoMemoryResponse])
async def list_photo_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's non-deleted photo memories."""
    try:
        return photo_memory_service.list_photo_memories(db, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{photo_memory_id}", response_model=PhotoMemoryResponse)
async def get_photo_memory(
    photo_memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get one current-user photo memory."""
    try:
        return photo_memory_service.get_photo_memory(db, current_user.id, photo_memory_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.delete("/{photo_memory_id}", response_model=PhotoMemoryDeleteResponse)
async def delete_photo_memory(
    photo_memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the photo file and soft-delete the metadata record."""
    try:
        photo_memory_service.delete_photo_memory(db, current_user.id, photo_memory_id)
        return PhotoMemoryDeleteResponse()
    except RemoryException as e:
        raise to_http_exception(e)
