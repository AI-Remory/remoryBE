from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    total: int
    skip: int
    limit: int
    items: List[T]


class MessageResponse(BaseModel):
    """Common message response."""

    status: str
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Common error response."""

    status: str = "error"
    message: str
    detail: Optional[str] = None
    code: str = "INTERNAL_ERROR"


class TimestampMixin(BaseModel):
    """Created and updated timestamps."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
