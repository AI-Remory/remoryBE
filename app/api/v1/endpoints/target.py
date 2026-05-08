"""Target API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.target import (
    TargetCreateRequest,
    TargetUpdateRequest,
    TargetResponse,
    TargetDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.target_service import target_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(
    prefix="/targets",
    tags=["target"],
)


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Target 생성"""
    try:
        target = target_service.create_target(db, current_user.id, target_data)
        return target
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("", response_model=PaginatedResponse[TargetResponse])
async def list_targets(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """사용자의 Target 목록 조회"""
    try:
        result = target_service.get_user_targets(db, current_user.id, skip, limit)
        return PaginatedResponse(
            total=result["total"],
            skip=skip,
            limit=limit,
            items=result["items"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{target_id}", response_model=TargetDetailResponse)
async def get_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Target 상세 조회"""
    try:
        detail = target_service.get_target_detail(db, target_id, current_user.id)
        target = detail["target"]

        return TargetDetailResponse(
            id=target.id,
            user_id=target.user_id,
            name=target.name,
            description=target.description,
            target_type=target.target_type,
            profile_image_path=target.profile_image_path,
            is_deleted=target.is_deleted,
            created_at=target.created_at,
            updated_at=target.updated_at,
            media_count=detail["media_count"],
            has_persona=detail["has_persona"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Target 수정"""
    try:
        target = target_service.update_target(db, target_id, current_user.id, target_data)
        return target
    except RemoryException as e:
        raise to_http_exception(e)


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Target 삭제"""
    try:
        target_service.delete_target(db, target_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)

