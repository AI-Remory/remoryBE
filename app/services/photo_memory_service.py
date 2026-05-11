"""PhotoMemory business logic."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.interview import PhotoMemory
from app.schemas.photo_memory import PhotoMemoryCreateRequest
from app.utils.exceptions import FileUploadException, ForbiddenException, NotFoundException


class PhotoMemoryService:
    """User photo memory upload, lookup, and deletion service."""

    @staticmethod
    def _backend_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _upload_root() -> Path:
        base = Path(settings.UPLOAD_DIR)
        if not base.is_absolute():
            base = PhotoMemoryService._backend_root() / base
        return base

    @staticmethod
    def _build_user_dir(user_id: int) -> Path:
        user_dir = PhotoMemoryService._upload_root() / "photo_memories" / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    @staticmethod
    def _validate_image(upload_file: UploadFile) -> None:
        if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
            raise FileUploadException("PhotoMemory upload must use an image/* MIME type")

    @staticmethod
    def _save_file(user_id: int, upload_file: UploadFile) -> tuple[str, str, int]:
        PhotoMemoryService._validate_image(upload_file)
        user_dir = PhotoMemoryService._build_user_dir(user_id)

        original_filename = Path(upload_file.filename or "upload.bin").name
        suffix = Path(original_filename).suffix
        stored_filename = f"{uuid4().hex}{suffix}"
        abs_path = user_dir / stored_filename

        file_bytes = upload_file.file.read()
        file_size = len(file_bytes)
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds maximum limit ({settings.MAX_UPLOAD_SIZE} bytes)")

        with abs_path.open("wb") as f:
            f.write(file_bytes)

        relative_path = abs_path.relative_to(PhotoMemoryService._backend_root()).as_posix()
        return stored_filename, relative_path, file_size

    @staticmethod
    def create_photo_memory(
        db: Session,
        user_id: int,
        photo_data: PhotoMemoryCreateRequest,
        upload_file: UploadFile,
    ) -> PhotoMemory:
        stored_filename, file_path, file_size = PhotoMemoryService._save_file(user_id, upload_file)
        photo_memory = PhotoMemory(
            user_id=user_id,
            title=photo_data.title,
            description=photo_data.description,
            file_path=file_path,
            original_filename=Path(upload_file.filename or "upload.bin").name,
            stored_filename=stored_filename,
            mime_type=upload_file.content_type,
            file_size=file_size,
            taken_at=photo_data.taken_at,
            location=photo_data.location,
        )
        db.add(photo_memory)
        db.commit()
        db.refresh(photo_memory)
        return photo_memory

    @staticmethod
    def list_photo_memories(db: Session, user_id: int) -> list[PhotoMemory]:
        return db.execute(
            select(PhotoMemory)
            .where(
                PhotoMemory.user_id == user_id,
                PhotoMemory.deleted_at.is_(None),
            )
            .order_by(PhotoMemory.created_at.desc(), PhotoMemory.id.desc())
        ).scalars().all()

    @staticmethod
    def get_photo_memory(db: Session, user_id: int, photo_memory_id: int) -> PhotoMemory:
        photo_memory = db.execute(
            select(PhotoMemory).where(
                PhotoMemory.id == photo_memory_id,
                PhotoMemory.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

        if not photo_memory:
            raise NotFoundException("PhotoMemory", photo_memory_id)
        if photo_memory.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this photo memory")
        return photo_memory

    @staticmethod
    def delete_photo_memory(db: Session, user_id: int, photo_memory_id: int) -> None:
        photo_memory = PhotoMemoryService.get_photo_memory(db, user_id, photo_memory_id)

        abs_path = PhotoMemoryService._backend_root() / photo_memory.file_path
        if abs_path.exists():
            abs_path.unlink()

        photo_memory.deleted_at = datetime.now(UTC)
        db.commit()


photo_memory_service = PhotoMemoryService()
