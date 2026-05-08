from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.sharing import SharePermission
from app.models.storybook import StoryBookVisibility
from app.schemas.common import TimestampMixin


class ShareLinkCreateRequest(BaseModel):
    expires_at: Optional[datetime] = None


class ShareLinkResponse(TimestampMixin):
    id: int
    storybook_id: int
    owner_id: int
    token: str
    is_active: bool
    expires_at: Optional[datetime]
    disabled_at: Optional[datetime]
    share_url: str

    class Config:
        from_attributes = True


class ShareLinkDisableResponse(BaseModel):
    id: int
    is_active: bool
    disabled_at: Optional[datetime]


class PublicStoryChapterResponse(BaseModel):
    title: str
    content: str
    summary: Optional[str]
    order_index: int


class PublicSharedStoryBookResponse(BaseModel):
    title: str
    summary: Optional[str]
    visibility: StoryBookVisibility
    chapters: list[PublicStoryChapterResponse]


class MemoryGroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class MemoryGroupResponse(TimestampMixin):
    id: int
    creator_id: int
    name: str
    description: Optional[str]
    group_code: str
    profile_image_path: Optional[str]

    class Config:
        from_attributes = True


class GroupMemberResponse(TimestampMixin):
    id: int
    group_id: int
    user_id: int
    permission: SharePermission

    class Config:
        from_attributes = True
