"""Helpers for serving local upload files through authenticated endpoints."""

import mimetypes
import os
from pathlib import Path

from fastapi.responses import FileResponse

from app.core.settings import settings
from app.utils.exceptions import ForbiddenException, NotFoundException


class ProtectedFileService:
    """Resolve DB file paths safely before returning FileResponse."""

    @staticmethod
    def _backend_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def upload_root() -> Path:
        base = Path(settings.UPLOAD_DIR)
        if not base.is_absolute():
            base = ProtectedFileService._backend_root() / base
        return base.resolve()

    @staticmethod
    def resolve_upload_file(file_path: str, resource_name: str, resource_id: int) -> Path:
        candidate = Path(file_path)
        if not candidate.is_absolute():
            candidate = ProtectedFileService._backend_root() / candidate

        resolved = candidate.resolve()
        upload_root = ProtectedFileService.upload_root()
        if resolved != upload_root and upload_root not in resolved.parents:
            raise ForbiddenException("Invalid upload file path")
        if not resolved.exists() or not resolved.is_file():
            raise NotFoundException(resource_name, resource_id)
        return resolved

    @staticmethod
    def response(
        file_path: str,
        resource_name: str,
        resource_id: int,
        media_type: str | None = None,
        filename: str | None = None,
    ) -> FileResponse:
        resolved = ProtectedFileService.resolve_upload_file(file_path, resource_name, resource_id)
        guessed_type = mimetypes.guess_type(resolved.name)[0]
        if media_type is None and resolved.suffix.lower() == ".webm":
            media_type = "audio/webm"

        return FileResponse(
            resolved,
            media_type=media_type or guessed_type or "application/octet-stream",
            filename=filename,
            stat_result=os.stat(resolved),
        )
