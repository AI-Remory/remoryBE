"""입증 요청 API"""
from fastapi import APIRouter, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.target_verification import VerificationType
from app.schemas.target_verification import (
    VerificationRequestResponse,
    VerificationRequestDetailResponse,
)
from app.schemas.common import PaginatedResponse
from app.services.verification_service import verification_service
from app.utils.exceptions import FileUploadException, RemoryException, ValidationException, to_http_exception

router = APIRouter(
    prefix="/targets",
    tags=["verification"],
)

detail_router = APIRouter(
    tags=["verification"],
)


@router.post(
    "/{target_id}/verification-requests",
    response_model=VerificationRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_verification_request(
    target_id: int,
    verification_type_param: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """입증 요청 생성 (파일 업로드)"""
    try:
        # 파일 저장
        file_info = await verification_service.save_verification_file(
            file,
            current_user.id,
        )

        # 입증 요청 생성
        try:
            verification_type = VerificationType(verification_type_param.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid verification type",
            ) from exc

        request = verification_service.create_verification_request(
            db,
            current_user.id,
            target_id,
            verification_type,
            file_info,
        )

        return request
    except (ValidationException, FileUploadException) as e:
        raise to_http_exception(e, status.HTTP_400_BAD_REQUEST)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get(
    "/{target_id}/verification-requests",
    response_model=PaginatedResponse[VerificationRequestResponse],
)
async def list_user_verification_requests(
    target_id: int,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """사용자의 입증 요청 목록 조회"""
    try:
        result = verification_service.get_user_verification_requests(
            db,
            current_user.id,
            target_id,
            skip,
            limit,
        )

        return PaginatedResponse(
            total=result["total"],
            skip=skip,
            limit=limit,
            items=result["items"],
        )
    except RemoryException as e:
        raise to_http_exception(e)


@detail_router.get(
    "/verification-requests/{request_id}",
    response_model=VerificationRequestDetailResponse,
)
async def get_verification_request_detail(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """입증 요청 상세 조회"""
    try:
        request = verification_service.get_verification_request(db, request_id)

        # 본인 또는 target 소유자만 조회 가능
        if request.user_id != current_user.id and request.target.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="접근 권한이 없습니다",
            )

        return request
    except RemoryException as e:
        raise to_http_exception(e)



