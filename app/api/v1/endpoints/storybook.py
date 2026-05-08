"""StoryBook API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.storybook import (
    StoryBookCreateRequest,
    StoryBookDetailResponse,
    StoryBookResponse,
    StoryChapterResponse,
)
from app.services.storybook_service import storybook_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/storybooks", tags=["storybook"])


@router.post("", response_model=StoryBookDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_storybook(
    storybook_data: StoryBookCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a mock storybook from an interview session or photo memory."""
    try:
        return await storybook_service.create_storybook(db, current_user.id, storybook_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=list[StoryBookResponse])
async def list_storybooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's non-deleted storybooks."""
    try:
        return storybook_service.list_storybooks(db, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{storybook_id}", response_model=StoryBookDetailResponse)
async def get_storybook(
    storybook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a storybook with non-deleted chapters."""
    try:
        return storybook_service.get_storybook(db, current_user.id, storybook_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{storybook_id}/chapters", response_model=list[StoryChapterResponse])
async def list_storybook_chapters(
    storybook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List non-deleted chapters in order_index ascending order."""
    try:
        return storybook_service.list_chapters(db, current_user.id, storybook_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.post("/{storybook_id}/regenerate", response_model=StoryBookDetailResponse)
async def regenerate_storybook(
    storybook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate a storybook from its linked source data."""
    try:
        return await storybook_service.regenerate_storybook(db, current_user.id, storybook_id)
    except RemoryException as e:
        raise to_http_exception(e)
