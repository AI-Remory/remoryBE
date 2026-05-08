from typing import Optional, List
from pydantic import BaseModel
from app.schemas.common import TimestampMixin


class StoryChapterResponse(TimestampMixin):
    """StoryChapter 응답"""
    id: int
    storybook_id: int
    chapter_order: int
    title: str
    content: str
    summary: Optional[str]

    class Config:
        from_attributes = True


class StoryVoiceNarrationResponse(TimestampMixin):
    """StoryVoiceNarration 응답"""
    id: int
    storybook_id: int
    chapter_id: Optional[int]
    narration_file_path: str
    narration_mime_type: str
    narration_duration_seconds: Optional[int]
    narration_type: str

    class Config:
        from_attributes = True


class StoryBookCreateRequest(BaseModel):
    """StoryBook 생성 요청"""
    target_id: Optional[int] = None
    title: str
    description: Optional[str] = None


class StoryBookResponse(TimestampMixin):
    """StoryBook 응답"""
    id: int
    user_id: int
    target_id: Optional[int]
    title: str
    description: Optional[str]
    cover_image_path: Optional[str]
    is_published: bool

    class Config:
        from_attributes = True


class StoryBookDetailResponse(StoryBookResponse):
    """StoryBook 상세 응답"""
    chapters: List[StoryChapterResponse]
    voice_narrations: List[StoryVoiceNarrationResponse]

