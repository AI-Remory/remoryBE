"""파일 관리 서비스"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile
from app.utils.constants import (
    UPLOAD_DIR,
    IMAGES_DIR,
    VOICES_DIR,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_AUDIO_EXTENSIONS,
    MAX_UPLOAD_SIZE,
)
from app.utils.exceptions import FileUploadException


class FileService:
    """파일 업로드/삭제 서비스"""

    @staticmethod
    def ensure_upload_dirs():
        """업로드 디렉토리 생성"""
        Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
        Path(VOICES_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    async def save_image_file(upload_file: UploadFile) -> dict:
        """이미지 파일 저장"""
        FileService.ensure_upload_dirs()

        # 파일 크기 확인
        contents = await upload_file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds maximum limit ({MAX_UPLOAD_SIZE} bytes)")

        # 파일 확장자 확인
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise FileUploadException(f"Invalid image format. Allowed: {ALLOWED_IMAGE_EXTENSIONS}")

        # 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(IMAGES_DIR, unique_filename)

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(contents)

        return {
            "file_path": file_path,
            "original_filename": upload_file.filename,
            "mime_type": upload_file.content_type,
            "file_size": len(contents),
        }

    @staticmethod
    async def save_audio_file(upload_file: UploadFile) -> dict:
        """음성 파일 저장"""
        FileService.ensure_upload_dirs()

        # 파일 크기 확인
        contents = await upload_file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise FileUploadException(f"File size exceeds maximum limit ({MAX_UPLOAD_SIZE} bytes)")

        # 파일 확장자 확인
        file_ext = Path(upload_file.filename).suffix.lower()
        if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise FileUploadException(f"Invalid audio format. Allowed: {ALLOWED_AUDIO_EXTENSIONS}")

        # 고유한 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(VOICES_DIR, unique_filename)

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(contents)

        return {
            "file_path": file_path,
            "original_filename": upload_file.filename,
            "mime_type": upload_file.content_type,
            "file_size": len(contents),
        }

    @staticmethod
    def delete_file(file_path: str):
        """파일 삭제"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            raise FileUploadException(f"Failed to delete file: {str(e)}")

    @staticmethod
    def delete_files(file_paths: list):
        """여러 파일 삭제"""
        for file_path in file_paths:
            FileService.delete_file(file_path)


file_service = FileService()

