from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.storybook import StoryBookSourceType, StoryBookStatus, StoryBookVisibility
from app.schemas.common import TimestampMixin


class StoryBookCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    interview_session_id: Optional[int] = None
    photo_memory_id: Optional[int] = None
    visibility: StoryBookVisibility = StoryBookVisibility.PRIVATE


class StoryChapterResponse(TimestampMixin):
    id: int
    storybook_id: int
    title: str
    content: str
    summary: Optional[str]
    order_index: int
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class StoryBookResponse(TimestampMixin):
    id: int
    user_id: int
    photo_memory_id: Optional[int]
    interview_session_id: Optional[int]
    title: str
    summary: Optional[str]
    source_type: StoryBookSourceType
    status: StoryBookStatus
    visibility: StoryBookVisibility
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class StoryBookDetailResponse(StoryBookResponse):
    chapters: list[StoryChapterResponse] = Field(default_factory=list)
