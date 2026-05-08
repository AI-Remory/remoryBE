from datetime import datetime
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """페이지네이션 파라미터"""
    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답"""
    total: int
    skip: int
    limit: int
    items: List[T]


class MessageResponse(BaseModel):
    """메시지 응답"""
    status: str
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = "error"
    message: str
    detail: Optional[str] = None
    code: str = "INTERNAL_ERROR"


class TimestampMixin(BaseModel):
    """생성/수정 시간 포함"""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

