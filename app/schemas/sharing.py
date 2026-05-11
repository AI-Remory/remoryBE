from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.sharing import GroupMemberRole, SharePermission
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

    model_config = ConfigDict(from_attributes=True)


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
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class MemoryGroupResponse(TimestampMixin):
    id: int
    owner_id: int
    name: str
    description: Optional[str]
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class MemoryGroupDetailResponse(MemoryGroupResponse):
    my_role: GroupMemberRole

    model_config = ConfigDict(from_attributes=True)


class GroupMemberCreateRequest(BaseModel):
    user_id: int
    role: GroupMemberRole = GroupMemberRole.MEMBER


class GroupMemberResponse(TimestampMixin):
    id: int
    group_id: int
    user_id: int
    role: GroupMemberRole
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class GroupStoryBookResponse(BaseModel):
    id: int
    group_id: int
    storybook_id: int
    shared_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupStoryBookListItemResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    visibility: StoryBookVisibility
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
