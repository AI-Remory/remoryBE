"""Target verification request service."""

from datetime import UTC, datetime
from pathlib import Path
import uuid
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditTargetType
from app.models.target import Target
from app.models.target_verification import TargetVerificationRequest, VerificationStatus, VerificationType
from app.utils.constants import MAX_UPLOAD_SIZE, UPLOAD_DIR
from app.utils.exceptions import FileUploadException, NotFoundException, ValidationException


class VerificationService:
    @staticmethod
    def _utcnow_naive() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _backend_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _upload_root() -> Path:
        base = Path(UPLOAD_DIR)
        if not base.is_absolute():
            base = VerificationService._backend_root() / base
        return base

    @staticmethod
    def _parse_status(value: str) -> VerificationStatus:
        normalized = value.strip().upper()
        return VerificationStatus[normalized]

    @staticmethod
    def _parse_verification_type(value: str) -> VerificationType:
        normalized = value.strip().upper()
        return VerificationType[normalized]

    @staticmethod
    def ensure_verification_upload_dir(user_id: int) -> Path:
        user_dir = VerificationService._upload_root() / "verifications" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @staticmethod
    async def save_verification_file(upload_file: UploadFile, user_id: int) -> dict:
        user_dir = VerificationService.ensure_verification_upload_dir(user_id)
        contents = await upload_file.read()

        if len(contents) > MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds limit ({MAX_UPLOAD_SIZE} bytes)")

        allowed_mimes = {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/jpg",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if upload_file.content_type not in allowed_mimes:
            raise FileUploadException("Unsupported file type. Allowed: PDF, image, document")

        file_ext = Path(upload_file.filename or "").suffix.lower()
        stored_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = user_dir / stored_filename
        file_path.write_bytes(contents)

        submitted_file_path = file_path.resolve().relative_to(VerificationService._backend_root()).as_posix()
        return {
            "submitted_file_path": submitted_file_path,
            "original_filename": upload_file.filename or stored_filename,
            "mime_type": upload_file.content_type,
            "file_size": len(contents),
        }

    @staticmethod
    def _get_owned_target(db: Session, target_id: int, user_id: int) -> Target:
        target = db.execute(
            select(Target).where(
                Target.id == target_id,
                Target.user_id == user_id,
                Target.is_deleted == False,
            )
        ).scalar_one_or_none()
        if target is None:
            raise NotFoundException("Target", target_id)
        return target

    @staticmethod
    def create_verification_request(
        db: Session,
        user_id: int,
        target_id: int,
        verification_type: VerificationType,
        file_info: dict,
        applicant_note: Optional[str] = None,
    ) -> TargetVerificationRequest:
        VerificationService._get_owned_target(db, target_id, user_id)

        existing = db.execute(
            select(TargetVerificationRequest).where(
                TargetVerificationRequest.target_id == target_id,
                TargetVerificationRequest.status.in_(
                    [VerificationStatus.PENDING, VerificationStatus.NEED_MORE_INFO]
                ),
                TargetVerificationRequest.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing:
            raise ValidationException("A verification request is already pending for this target")

        request = TargetVerificationRequest(
            user_id=user_id,
            target_id=target_id,
            verification_type=verification_type,
            status=VerificationStatus.PENDING,
            submitted_file_path=file_info["submitted_file_path"],
            original_filename=file_info["original_filename"],
            mime_type=file_info["mime_type"],
            file_size=file_info["file_size"],
            applicant_note=applicant_note,
            submitted_at=VerificationService._utcnow_naive(),
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def get_verification_request(db: Session, request_id: int) -> TargetVerificationRequest:
        request = db.execute(
            select(TargetVerificationRequest).where(
                TargetVerificationRequest.id == request_id,
                TargetVerificationRequest.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if request is None:
            raise NotFoundException("TargetVerificationRequest", request_id)
        return request

    @staticmethod
    def get_user_verification_requests(
        db: Session,
        user_id: int,
        target_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        VerificationService._get_owned_target(db, target_id, user_id)

        query = (
            select(TargetVerificationRequest)
            .where(
                TargetVerificationRequest.target_id == target_id,
                TargetVerificationRequest.deleted_at.is_(None),
            )
            .order_by(TargetVerificationRequest.created_at.desc(), TargetVerificationRequest.id.desc())
        )
        count_query = select(func.count(TargetVerificationRequest.id)).where(
            TargetVerificationRequest.target_id == target_id,
            TargetVerificationRequest.deleted_at.is_(None),
        )

        return {
            "total": db.execute(count_query).scalar_one() or 0,
            "items": db.execute(query.offset(skip).limit(limit)).scalars().all(),
        }

    @staticmethod
    def get_admin_verification_requests(
        db: Session,
        status: Optional[VerificationStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        query = select(TargetVerificationRequest).where(TargetVerificationRequest.deleted_at.is_(None))
        count_query = select(func.count(TargetVerificationRequest.id)).where(
            TargetVerificationRequest.deleted_at.is_(None)
        )

        if status is not None:
            query = query.where(TargetVerificationRequest.status == status)
            count_query = count_query.where(TargetVerificationRequest.status == status)

        query = query.order_by(TargetVerificationRequest.created_at.desc(), TargetVerificationRequest.id.desc())
        offset = (page - 1) * size
        return {
            "total": db.execute(count_query).scalar_one() or 0,
            "items": db.execute(query.offset(offset).limit(size)).scalars().all(),
            "page": page,
            "size": size,
        }

    @staticmethod
    def _record_admin_decision_audit(
        db: Session,
        request: TargetVerificationRequest,
        admin_user_id: int,
        action: str,
    ) -> None:
        """Record an audit log for verification admin decision.

        Args:
            db: Database session
            request: The verification request
            admin_user_id: Admin user ID
            action: The action taken (approve, reject, need_more_info, revoke)
        """
        try:
            from app.services.audit_log_service import AuditLogService

            action_map = {
                "approve": AuditAction.VERIFICATION_APPROVED,
                "reject": AuditAction.VERIFICATION_REJECTED,
                "need_more_info": AuditAction.VERIFICATION_NEED_MORE_INFO,
                "revoke": AuditAction.VERIFICATION_REVOKED,
            }

            audit_action = action_map.get(action, AuditAction.VERIFICATION_APPROVED)

            AuditLogService.create_audit_log(
                db=db,
                action=audit_action,
                actor_user_id=admin_user_id,
                target_type=AuditTargetType.VERIFICATION_REQUEST,
                target_id=request.id,
                description=f"Verification request {action} - Target: {request.target_id}",
                metadata={"verification_type": request.verification_type.value, "request_id": request.id},
            )
        except Exception:
            # Don't let audit log creation failures break the main flow
            pass

    @staticmethod
    def approve_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
        admin_note: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> TargetVerificationRequest:
        request = VerificationService.get_verification_request(db, request_id)
        if request.status not in (VerificationStatus.PENDING, VerificationStatus.NEED_MORE_INFO):
            raise ValidationException("Only pending requests can be approved")

        request.status = VerificationStatus.APPROVED
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id
        request.admin_note = admin_note
        request.rejection_reason = None
        request.expires_at = expires_at
        VerificationService._record_admin_decision_audit(db, request, admin_user_id, "approve")

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def reject_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
        rejection_reason: str,
        admin_note: Optional[str] = None,
    ) -> TargetVerificationRequest:
        request = VerificationService.get_verification_request(db, request_id)
        if request.status not in (VerificationStatus.PENDING, VerificationStatus.NEED_MORE_INFO):
            raise ValidationException("Only pending requests can be rejected")

        request.status = VerificationStatus.REJECTED
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id
        request.rejection_reason = rejection_reason
        request.admin_note = admin_note
        VerificationService._record_admin_decision_audit(db, request, admin_user_id, "reject")

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def need_more_info_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
        admin_note: str,
    ) -> TargetVerificationRequest:
        request = VerificationService.get_verification_request(db, request_id)
        if request.status != VerificationStatus.PENDING:
            raise ValidationException("Only pending requests can be marked as needing more info")

        request.status = VerificationStatus.NEED_MORE_INFO
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id
        request.admin_note = admin_note
        VerificationService._record_admin_decision_audit(db, request, admin_user_id, "need_more_info")

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def revoke_verification_request(
        db: Session,
        request_id: int,
        admin_user_id: int,
        admin_note: Optional[str] = None,
    ) -> TargetVerificationRequest:
        request = VerificationService.get_verification_request(db, request_id)
        if request.status != VerificationStatus.APPROVED:
            raise ValidationException("Only approved requests can be revoked")

        request.status = VerificationStatus.REVOKED
        request.reviewed_at = VerificationService._utcnow_naive()
        request.reviewed_by = admin_user_id
        request.admin_note = admin_note
        VerificationService._record_admin_decision_audit(db, request, admin_user_id, "revoke")

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def get_approved_verification_for_target(
        db: Session,
        target_id: int,
    ) -> TargetVerificationRequest | None:
        now = VerificationService._utcnow_naive()
        return db.execute(
            select(TargetVerificationRequest).where(
                and_(
                    TargetVerificationRequest.target_id == target_id,
                    TargetVerificationRequest.status == VerificationStatus.APPROVED,
                    TargetVerificationRequest.deleted_at.is_(None),
                    or_(
                        TargetVerificationRequest.expires_at.is_(None),
                        TargetVerificationRequest.expires_at > now,
                    ),
                )
            )
        ).scalars().first()

    @staticmethod
    def resolve_submitted_file_path(request: TargetVerificationRequest) -> Path:
        path = Path(request.submitted_file_path)
        if not path.is_absolute():
            path = VerificationService._backend_root() / path

        resolved = path.resolve()
        upload_root = VerificationService._upload_root().resolve()
        if upload_root not in resolved.parents:
            raise ValidationException("Invalid verification file path")
        if not resolved.exists() or not resolved.is_file():
            raise NotFoundException("Verification file", request.id)
        return resolved


verification_service = VerificationService()
