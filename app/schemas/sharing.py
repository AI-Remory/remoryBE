from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.sharing import SharePermission


class ShareLinkCreateRequest(BaseModel):
    """공유 링크 생성 요청"""
    storybook_id: int
    permission: SharePermission = SharePermission.VIEW
    description: Optional[str] = None


class ShareLinkResponse(TimestampMixin):
    """공유 링크 응답"""
    id: int
    storybook_id: int
    share_token: str
    permission: SharePermission
    description: Optional[str]
    is_expired: bool

    class Config:
        from_attributes = True


class MemoryGroupCreateRequest(BaseModel):
    """MemoryGroup 생성 요청"""
    name: str
    description: Optional[str] = None


class MemoryGroupResponse(TimestampMixin):
    """MemoryGroup 응답"""
    id: int
    creator_id: int
    name: str
    description: Optional[str]
    group_code: str
    profile_image_path: Optional[str]

    class Config:
        from_attributes = True


class GroupMemberResponse(TimestampMixin):
    """GroupMember 응답"""
    id: int
    group_id: int
    user_id: int
    permission: SharePermission

    class Config:
        from_attributes = True

