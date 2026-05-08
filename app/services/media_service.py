"""Target Media 관리 서비스"""
from pathlib import Path
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import UploadFile
from app.core.settings import settings
from app.models.media import TargetMedia, MediaType
from app.models.target import Target
from app.services.target_service import target_service
from app.utils.exceptions import NotFoundException, ForbiddenException, ValidationException, FileUploadException


class MediaService:
    """Target 미디어 업로드/조회/삭제"""

    @staticmethod
    def _backend_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _upload_root() -> Path:
        base = Path(settings.UPLOAD_DIR)
        if not base.is_absolute():
            base = MediaService._backend_root() / base
        return base

    @staticmethod
    def _build_target_dir(media_type: MediaType, target_id: int) -> Path:
        root = MediaService._upload_root()
        folder = "images" if media_type == MediaType.IMAGE else "voices"
        target_dir = root / folder / str(target_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @staticmethod
    def _validate_mime(media_type: MediaType, mime_type: str | None) -> None:
        if not mime_type:
            raise ValidationException("Missing mime type")

        if media_type == MediaType.IMAGE and not mime_type.startswith("image/"):
            raise ValidationException("Image upload must use an image/* MIME type")
        if media_type == MediaType.VOICE and not mime_type.startswith("audio/"):
            raise ValidationException("Voice upload must use an audio/* MIME type")

    @staticmethod
    def _save_file(target_id: int, media_type: MediaType, upload_file: UploadFile) -> tuple[str, int, str]:
        MediaService._validate_mime(media_type, upload_file.content_type)
        target_dir = MediaService._build_target_dir(media_type, target_id)

        original_filename = Path(upload_file.filename or "upload.bin").name
        suffix = Path(original_filename).suffix
        stored_filename = f"{uuid4().hex}{suffix}"
        abs_path = target_dir / stored_filename

        file_bytes = upload_file.file.read()
        file_size = len(file_bytes)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds maximum limit ({settings.MAX_UPLOAD_SIZE} bytes)")

        with abs_path.open("wb") as f:
            f.write(file_bytes)

        relative_path = abs_path.relative_to(MediaService._backend_root()).as_posix()
        return stored_filename, file_size, relative_path

    @staticmethod
    def upload_target_media(
        db: Session,
        user_id: int,
        target_id: int,
        media_type: MediaType,
        upload_file: UploadFile,
    ) -> TargetMedia:
        """타겟 미디어 업로드"""
        target_service.get_target_by_id(db, target_id, user_id)

        stored_filename, file_size, file_path = MediaService._save_file(target_id, media_type, upload_file)
        media = TargetMedia(
            target_id=target_id,
            uploaded_by=user_id,
            media_type=media_type,
            original_filename=Path(upload_file.filename or "upload.bin").name,
            stored_filename=stored_filename,
            file_path=file_path,
            mime_type=upload_file.content_type,
            file_size=file_size,
        )
        db.add(media)
        db.commit()
        db.refresh(media)
        return media

    @staticmethod
    def get_target_media_list(db: Session, user_id: int, target_id: int) -> list[TargetMedia]:
        """타겟 미디어 목록 조회"""
        target_service.get_target_by_id(db, target_id, user_id)

        return db.execute(
            select(TargetMedia)
            .where(TargetMedia.target_id == target_id, TargetMedia.is_deleted == False)
            .order_by(TargetMedia.created_at.desc())
        ).scalars().all()

    @staticmethod
    def _resolve_media_for_user(db: Session, user_id: int, media_id: int) -> TargetMedia:
        media = db.execute(
            select(TargetMedia).where(TargetMedia.id == media_id, TargetMedia.is_deleted == False)
        ).scalar_one_or_none()

        if not media:
            raise NotFoundException("TargetMedia", media_id)

        target = db.execute(select(Target).where(Target.id == media.target_id)).scalar_one_or_none()
        if not target:
            raise NotFoundException("Target", media.target_id)
        if target.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this media")
        return media

    @staticmethod
    def delete_media(db: Session, user_id: int, media_id: int) -> None:
        """미디어 삭제 (파일 + DB)"""
        media = MediaService._resolve_media_for_user(db, user_id, media_id)

        abs_path = MediaService._backend_root() / media.file_path
        if abs_path.exists():
            abs_path.unlink()

        db.delete(media)
        db.commit()


media_service = MediaService()

