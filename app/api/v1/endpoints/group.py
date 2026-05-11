"""MemoryGroup API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.sharing import (
    GroupMemberCreateRequest,
    GroupMemberResponse,
    GroupStoryBookListItemResponse,
    GroupStoryBookResponse,
    MemoryGroupCreateRequest,
    MemoryGroupDetailResponse,
    MemoryGroupResponse,
)
from app.services.group_service import group_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/groups", tags=["group"])


@router.post("", response_model=MemoryGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: MemoryGroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a memory group and add the creator as OWNER."""
    try:
        return group_service.create_group(db, current_user.id, group_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=list[MemoryGroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List groups where the current user is an active member."""
    try:
        return group_service.list_groups(db, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{group_id}", response_model=MemoryGroupDetailResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get group detail with the current user's role."""
    try:
        return group_service.get_group_detail(db, group_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.post("/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: int,
    member_data: GroupMemberCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a group member. Only OWNER can add members."""
    try:
        return group_service.add_member(db, group_id, current_user.id, member_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_group_members(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active members of a group."""
    try:
        return group_service.list_members(db, group_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.post(
    "/{group_id}/storybooks/{storybook_id}",
    response_model=GroupStoryBookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def share_storybook_to_group(
    group_id: int,
    storybook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Share the current user's storybook to a group."""
    try:
        return group_service.share_storybook(db, group_id, storybook_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{group_id}/storybooks", response_model=list[GroupStoryBookListItemResponse])
async def list_group_storybooks(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List non-deleted storybooks shared to a group."""
    try:
        return group_service.list_storybooks(db, group_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)
