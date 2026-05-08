from fastapi import HTTPException, status


class RemoryException(Exception):
    """기본 Remory 예외"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class NotFoundException(RemoryException):
    """리소스를 찾을 수 없을 때"""
    def __init__(self, resource: str, resource_id: int = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, "NOT_FOUND")


class UnauthorizedException(RemoryException):
    """인증 실패"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenException(RemoryException):
    """권한 없음"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN")


class ValidationException(RemoryException):
    """검증 실패"""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class FileUploadException(RemoryException):
    """파일 업로드 실패"""
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, "FILE_UPLOAD_ERROR")


def to_http_exception(exc: RemoryException, status_code: int = None):
    """RemoryException을 HTTPException으로 변환"""
    if status_code is None:
        if isinstance(exc, NotFoundException):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, UnauthorizedException):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, ForbiddenException):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ValidationException):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        else:
            status_code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=status_code,
        detail=exc.message,
    )

