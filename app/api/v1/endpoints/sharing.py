"""ShareLink API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.sharing import (
    PublicSharedStoryBookResponse,
    ShareLinkCreateRequest,
    ShareLinkDisableResponse,
    ShareLinkResponse,
)
from app.services.share_service import share_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["sharing"])


@router.post(
    "/storybooks/{storybook_id}/share-links",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_share_link(
    storybook_id: int,
    share_data: ShareLinkCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a token share link for the current user's storybook."""
    try:
        return share_service.create_share_link(
            db=db,
            user_id=current_user.id,
            storybook_id=storybook_id,
            share_data=share_data or ShareLinkCreateRequest(),
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/storybooks/{storybook_id}/share-links", response_model=list[ShareLinkResponse])
async def list_share_links(
    storybook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List share links for the current user's storybook."""
    try:
        return share_service.list_share_links(db, current_user.id, storybook_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/share/{token}", response_model=PublicSharedStoryBookResponse)
async def get_shared_storybook(
    token: str,
    db: Session = Depends(get_db),
):
    """Read a storybook through a public token link."""
    try:
        return share_service.get_public_storybook(db, token)
    except RemoryException as e:
        raise to_http_exception(e)


@router.patch("/share-links/{share_link_id}/disable", response_model=ShareLinkDisableResponse)
async def disable_share_link(
    share_link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disable a share link owned by the current user."""
    try:
        return share_service.disable_share_link(db, current_user.id, share_link_id)
    except RemoryException as e:
        raise to_http_exception(e)
