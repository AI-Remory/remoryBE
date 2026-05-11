"""MemoryGroup business logic."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sharing import GroupMember, GroupMemberRole, GroupStoryBook, MemoryGroup
from app.models.storybook import StoryBook, StoryBookVisibility
from app.models.user import User
from app.schemas.sharing import GroupMemberCreateRequest, MemoryGroupCreateRequest
from app.models.consent import ConsentType
from app.services.consent_service import consent_service
from app.utils.exceptions import ForbiddenException, NotFoundException


class GroupService:
    """Memory group, member, and group storybook sharing service."""

    @staticmethod
    def _get_active_member(db: Session, group_id: int, user_id: int) -> GroupMember | None:
        return db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

    @staticmethod
    def _get_group(db: Session, group_id: int) -> MemoryGroup:
        group = db.execute(
            select(MemoryGroup).where(
                MemoryGroup.id == group_id,
                MemoryGroup.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not group:
            raise NotFoundException("MemoryGroup", group_id)
        return group

    @staticmethod
    def _get_accessible_group(db: Session, group_id: int, user_id: int) -> tuple[MemoryGroup, GroupMember]:
        group = GroupService._get_group(db, group_id)
        member = GroupService._get_active_member(db, group_id, user_id)
        if not member:
            raise ForbiddenException("You don't have permission to access this group")
        return group, member

    @staticmethod
    def _get_owner_group(db: Session, group_id: int, user_id: int) -> MemoryGroup:
        group, member = GroupService._get_accessible_group(db, group_id, user_id)
        if member.role != GroupMemberRole.OWNER:
            raise ForbiddenException("Only group owners can manage members")
        return group

    @staticmethod
    def create_group(db: Session, user_id: int, group_data: MemoryGroupCreateRequest) -> MemoryGroup:
        group = MemoryGroup(
            owner_id=user_id,
            name=group_data.name,
            description=group_data.description,
        )
        db.add(group)
        db.flush()
        db.add(
            GroupMember(
                group_id=group.id,
                user_id=user_id,
                role=GroupMemberRole.OWNER,
            )
        )
        db.commit()
        db.refresh(group)
        return group

    @staticmethod
    def list_groups(db: Session, user_id: int) -> list[MemoryGroup]:
        return db.execute(
            select(MemoryGroup)
            .join(GroupMember, GroupMember.group_id == MemoryGroup.id)
            .where(
                GroupMember.user_id == user_id,
                GroupMember.deleted_at.is_(None),
                MemoryGroup.deleted_at.is_(None),
            )
            .order_by(MemoryGroup.created_at.desc(), MemoryGroup.id.desc())
        ).scalars().all()

    @staticmethod
    def get_group_detail(db: Session, group_id: int, user_id: int) -> dict:
        group, member = GroupService._get_accessible_group(db, group_id, user_id)
        return {
            "id": group.id,
            "owner_id": group.owner_id,
            "name": group.name,
            "description": group.description,
            "deleted_at": group.deleted_at,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "my_role": member.role,
        }

    @staticmethod
    def add_member(
        db: Session,
        group_id: int,
        user_id: int,
        member_data: GroupMemberCreateRequest,
    ) -> GroupMember:
        GroupService._get_owner_group(db, group_id, user_id)

        target_user = db.execute(select(User).where(User.id == member_data.user_id)).scalar_one_or_none()
        if not target_user:
            raise NotFoundException("User", member_data.user_id)

        existing_member = db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == member_data.user_id,
                GroupMember.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing_member:
            return existing_member

        member = GroupMember(
            group_id=group_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def list_members(db: Session, group_id: int, user_id: int) -> list[GroupMember]:
        GroupService._get_accessible_group(db, group_id, user_id)
        return db.execute(
            select(GroupMember)
            .where(
                GroupMember.group_id == group_id,
                GroupMember.deleted_at.is_(None),
            )
            .order_by(GroupMember.created_at.asc(), GroupMember.id.asc())
        ).scalars().all()

    @staticmethod
    def share_storybook(db: Session, group_id: int, storybook_id: int, user_id: int) -> GroupStoryBook:
        GroupService._get_accessible_group(db, group_id, user_id)

        storybook = db.execute(
            select(StoryBook).where(
                StoryBook.id == storybook_id,
                StoryBook.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not storybook:
            raise NotFoundException("StoryBook", storybook_id)
        if storybook.user_id != user_id:
            raise ForbiddenException("You can only share your own storybooks")

        consent_service.check_consent(db, user_id, None, ConsentType.GROUP_SHARE_CONSENT)

        existing_share = db.execute(
            select(GroupStoryBook).where(
                GroupStoryBook.group_id == group_id,
                GroupStoryBook.storybook_id == storybook_id,
                GroupStoryBook.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if existing_share:
            return existing_share

        storybook.visibility = StoryBookVisibility.GROUP
        group_storybook = GroupStoryBook(
            group_id=group_id,
            storybook_id=storybook_id,
            shared_by=user_id,
        )
        db.add(group_storybook)
        db.commit()
        db.refresh(group_storybook)
        return group_storybook

    @staticmethod
    def list_storybooks(db: Session, group_id: int, user_id: int) -> list[dict]:
        GroupService._get_accessible_group(db, group_id, user_id)
        rows = db.execute(
            select(GroupStoryBook, StoryBook)
            .join(StoryBook, StoryBook.id == GroupStoryBook.storybook_id)
            .where(
                GroupStoryBook.group_id == group_id,
                GroupStoryBook.deleted_at.is_(None),
                StoryBook.deleted_at.is_(None),
            )
            .order_by(GroupStoryBook.created_at.desc(), GroupStoryBook.id.desc())
        ).all()
        return [
            {
                "id": storybook.id,
                "title": storybook.title,
                "summary": storybook.summary,
                "visibility": storybook.visibility,
                "created_at": group_storybook.created_at,
            }
            for group_storybook, storybook in rows
        ]


group_service = GroupService()
