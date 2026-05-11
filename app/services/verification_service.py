"""입증 요청 서비스"""
import os
import uuid
from datetime import datetime, UTC
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.target_verification import TargetVerificationRequest, VerificationStatus, VerificationType
from app.models.target import Target
from app.utils.exceptions import NotFoundException, ValidationException, FileUploadException
from app.utils.constants import UPLOAD_DIR, MAX_UPLOAD_SIZE

VERIFICATION_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "verifications")


class VerificationService:
    """입증 요청 관리 서비스"""

    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def ensure_verification_upload_dir(user_id: int):
        """사용자별 업로드 디렉토리 생성"""
        user_dir = os.path.join(VERIFICATION_UPLOAD_DIR, str(user_id))
        Path(user_dir).mkdir(parents=True, exist_ok=True)
        return user_dir

    @staticmethod
    async def save_verification_file(
        upload_file: UploadFile,
        user_id: int,
    ) -> dict:
        """입증 파일 저장"""
        user_dir = VerificationService.ensure_verification_upload_dir(user_id)

        # 파일 크기 확인
        contents = await upload_file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise FileUploadException(f"파일 크기가 제한을 초과했습니다 ({MAX_UPLOAD_SIZE} bytes)")

        # 파일 MIME 타입 제한 (문서 파일만 허용)
        allowed_mimes = {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/jpg",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if upload_file.content_type not in allowed_mimes:
            raise FileUploadException(f"지원하지 않는 파일 형식입니다. 허용: PDF, 이미지, 문서")

        # UUID 기반 파일명 생성
        file_ext = Path(upload_file.filename).suffix.lower()
        stored_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(user_dir, stored_filename)

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(contents)

        document_file_path = os.path.relpath(file_path, UPLOAD_DIR)

        return {
            "document_file_path": document_file_path,
            "original_filename": upload_file.filename,
            "stored_filename": stored_filename,
            "mime_type": upload_file.content_type,
            "file_size": len(contents),
        }

    @staticmethod
    def create_verification_request(
        db: Session,
        user_id: int,
        target_id: int,
        verification_type: VerificationType,
        file_info: dict,
    ) -> TargetVerificationRequest:
        """입증 요청 생성"""
        # Target 존재 확인
        target = db.execute(
            select(Target).where(
                and_(
                    Target.id == target_id,
                    Target.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

        if not target:
            raise NotFoundException("Target을 찾을 수 없거나 권한이 없습니다")

        # 이미 미결정 상태의 요청이 있으면 거절
        existing = db.execute(
            select(TargetVerificationRequest).where(
                and_(
                    TargetVerificationRequest.target_id == target_id,
                    TargetVerificationRequest.status == VerificationStatus.PENDING,
                    TargetVerificationRequest.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValidationException("이미 검토 대기 중인 입증 요청이 있습니다")

        request = TargetVerificationRequest(
            user_id=user_id,
            target_id=target_id,
            verification_type=verification_type,
            status=VerificationStatus.PENDING,
            document_file_path=file_info["document_file_path"],
            original_filename=file_info["original_filename"],
            stored_filename=file_info["stored_filename"],
            mime_type=file_info["mime_type"],
            file_size=file_info["file_size"],
            submitted_at=VerificationService._utcnow_naive(),
        )

        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def get_verification_request(
        db: Session,
        request_id: int,
    ) -> TargetVerificationRequest:
        """입증 요청 조회"""
        request = db.execute(
            select(TargetVerificationRequest).where(
                TargetVerificationRequest.id == request_id
            )
        ).scalar_one_or_none()

        if not request or request.deleted_at is not None:
            raise NotFoundException("입증 요청을 찾을 수 없습니다")

        return request

    @staticmethod
    def get_user_verification_requests(
        db: Session,
        user_id: int,
        target_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """사용자의 특정 Target에 대한 입증 요청 목록 조회"""
        # Target 권한 확인
        target = db.execute(
            select(Target).where(
                and_(
                    Target.id == target_id,
                    Target.user_id == user_id,
                )
            )
        ).scalar_one_or_none()

        if not target:
            raise NotFoundException("Target을 찾을 수 없거나 권한이 없습니다")

        # 요청 목록 조회
        query = select(TargetVerificationRequest).where(
            and_(
                TargetVerificationRequest.target_id == target_id,
                TargetVerificationRequest.deleted_at.is_(None),
            )
        )

        total = db.execute(
            select(TargetVerificationRequest).where(
                and_(
                    TargetVerificationRequest.target_id == target_id,
                    TargetVerificationRequest.deleted_at.is_(None),
                )
            )
        ).scalars().all()
        total_count = len(total)

        items = db.execute(
            query.offset(skip).limit(limit)
        ).scalars().all()

        return {
            "total": total_count,
            "items": items,
        }

    @staticmethod
    def get_pending_verification_requests(
        db: Session,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """미검토 입증 요청 목록 조회 (관리자용)"""
        query = select(TargetVerificationRequest).where(
            and_(
                TargetVerificationRequest.status == VerificationStatus.PENDING,
                TargetVerificationRequest.deleted_at.is_(None),
            )
        )

        total = db.execute(query).scalars().all()
        total_count = len(total)

        items = db.execute(
            query.offset(skip).limit(limit).order_by(TargetVerificationRequest.submitted_at.desc())
        ).scalars().all()

        return {
            "total": total_count,
            "items": items,
        }

    @staticmethod
    def approve_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
    ) -> TargetVerificationRequest:
        """입증 요청 승인"""
        request = VerificationService.get_verification_request(db, request_id)

        if request.status != VerificationStatus.PENDING:
            raise ValidationException("대기 중인 요청만 승인할 수 있습니다")

        request.status = VerificationStatus.APPROVED
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
        rejection_reason: str,
    ) -> TargetVerificationRequest:
        """입증 요청 거절"""
        request = VerificationService.get_verification_request(db, request_id)

        if request.status != VerificationStatus.PENDING:
            raise ValidationException("대기 중인 요청만 거절할 수 있습니다")

        request.status = VerificationStatus.REJECTED
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id
        request.rejection_reason = rejection_reason

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def get_approved_verification_for_target(
        db: Session,
        target_id: int,
    ) -> TargetVerificationRequest:
        """Target의 승인된 입증 요청 조회"""
        request = db.execute(
            select(TargetVerificationRequest).where(
                and_(
                    TargetVerificationRequest.target_id == target_id,
                    TargetVerificationRequest.status == VerificationStatus.APPROVED,
                    TargetVerificationRequest.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

        return request

    @staticmethod
    def delete_verification_file(file_path: str):
        """입증 파일 삭제"""
        try:
            full_path = os.path.join(UPLOAD_DIR, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            # 파일 삭제 실패는 무시
            pass


verification_service = VerificationService()


