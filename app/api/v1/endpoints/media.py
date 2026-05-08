"""Target Media API"""
from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.media import MediaType
from app.schemas.media import TargetMediaResponse, MediaUploadResponse, MediaDeleteResponse
from app.services.media_service import media_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["media"])


@router.post("/targets/{target_id}/media", response_model=MediaUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_target_media(
    target_id: int,
    media_type: MediaType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """타겟 미디어 업로드"""
    try:
        media = media_service.upload_target_media(
            db=db,
            user_id=current_user.id,
            target_id=target_id,
            media_type=media_type,
            upload_file=file,
        )
        return MediaUploadResponse(
            file_id=media.id,
            target_id=media.target_id,
            uploaded_by=media.uploaded_by,
            original_filename=media.original_filename,
            stored_filename=media.stored_filename,
            file_path=media.file_path,
            media_type=media.media_type,
            file_size=media.file_size,
            mime_type=media.mime_type,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/targets/{target_id}/media", response_model=List[TargetMediaResponse])
async def list_target_media(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """타겟 미디어 목록 조회"""
    try:
        media_list = media_service.get_target_media_list(
            db=db,
            user_id=current_user.id,
            target_id=target_id,
        )
        return media_list
    except RemoryException as e:
        raise to_http_exception(e)


@router.delete("/media/{media_id}", response_model=MediaDeleteResponse)
async def delete_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """미디어 삭제 (파일 + DB)"""
    try:
        media_service.delete_media(db=db, user_id=current_user.id, media_id=media_id)
        return MediaDeleteResponse()
    except RemoryException as e:
        raise to_http_exception(e)

