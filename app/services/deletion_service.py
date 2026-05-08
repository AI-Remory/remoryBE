"""DeletionRequest business logic."""

import os
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import PersonaChat, PersonaMessage
from app.models.deletion import DeletionRequest, DeletionStatus, DeletionTargetType
from app.models.interview import PhotoMemory
from app.models.media import TargetMedia
from app.models.persona import Persona
from app.models.sharing import GroupMember, GroupStoryBook, MemoryGroup, ShareLink
from app.models.storybook import StoryBook, StoryChapter
from app.models.target import Target
from app.schemas.deletion import DeletionRequestCreateRequest
from app.utils.exceptions import ForbiddenException, NotFoundException


class DeletionService:
    """Create deletion requests and process them immediately for MVP."""

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _backend_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _delete_file_if_exists(relative_path: str | None) -> None:
        if not relative_path:
            return
        abs_path = DeletionService._backend_root() / relative_path
        if os.path.exists(abs_path):
            os.remove(abs_path)

    @staticmethod
    def create_deletion_request(
        db: Session,
        user_id: int,
        request_data: DeletionRequestCreateRequest,
    ) -> DeletionRequest:
        DeletionService._assert_ownership(
            db=db,
            user_id=user_id,
            target_type=request_data.target_type,
            target_id=request_data.target_id,
        )

        deletion_request = DeletionRequest(
            user_id=user_id,
            target_type=request_data.target_type,
            target_id=request_data.target_id,
            reason=request_data.reason,
            status=DeletionStatus.REQUESTED,
        )
        db.add(deletion_request)
        db.commit()
        db.refresh(deletion_request)

        request_id = deletion_request.id
        try:
            DeletionService._process_deletion(
                db=db,
                user_id=user_id,
                target_type=request_data.target_type,
                target_id=request_data.target_id,
            )
            deletion_request = db.get(DeletionRequest, request_id)
            deletion_request.status = DeletionStatus.COMPLETED
            deletion_request.processed_at = DeletionService._now()
            deletion_request.error_message = None
            db.commit()
            db.refresh(deletion_request)
            return deletion_request
        except Exception as exc:
            db.rollback()
            deletion_request = db.get(DeletionRequest, request_id)
            deletion_request.status = DeletionStatus.FAILED
            deletion_request.processed_at = DeletionService._now()
            deletion_request.error_message = str(exc)
            db.commit()
            db.refresh(deletion_request)
            return deletion_request

    @staticmethod
    def list_deletion_requests(db: Session, user_id: int) -> list[DeletionRequest]:
        return db.execute(
            select(DeletionRequest)
            .where(DeletionRequest.user_id == user_id)
            .order_by(DeletionRequest.created_at.desc(), DeletionRequest.id.desc())
        ).scalars().all()

    @staticmethod
    def get_deletion_request(db: Session, user_id: int, request_id: int) -> DeletionRequest:
        deletion_request = db.execute(
            select(DeletionRequest).where(DeletionRequest.id == request_id)
        ).scalar_one_or_none()
        if not deletion_request:
            raise NotFoundException("DeletionRequest", request_id)
        if deletion_request.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this deletion request")
        return deletion_request

    @staticmethod
    def _assert_ownership(db: Session, user_id: int, target_type: DeletionTargetType, target_id: int) -> None:
        DeletionService._resolve_owned_target(db, user_id, target_type, target_id)

    @staticmethod
    def _resolve_owned_target(db: Session, user_id: int, target_type: DeletionTargetType, target_id: int):
        if target_type == DeletionTargetType.TARGET:
            item = db.execute(select(Target).where(Target.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "Target", target_id, item.user_id if item else None, user_id)

        if target_type == DeletionTargetType.TARGET_MEDIA:
            item = db.execute(select(TargetMedia).where(TargetMedia.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(
                item, "TargetMedia", target_id, item.uploaded_by if item else None, user_id
            )

        if target_type == DeletionTargetType.PERSONA:
            item = db.execute(
                select(Persona).join(Target, Target.id == Persona.target_id).where(Persona.id == target_id)
            ).scalar_one_or_none()
            owner_id = item.target.user_id if item and item.target else None
            return DeletionService._require_owner(item, "Persona", target_id, owner_id, user_id)

        if target_type == DeletionTargetType.PERSONA_CHAT:
            item = db.execute(select(PersonaChat).where(PersonaChat.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "PersonaChat", target_id, item.user_id if item else None, user_id)

        if target_type == DeletionTargetType.PERSONA_MESSAGE:
            item = db.execute(
                select(PersonaMessage).join(PersonaChat, PersonaChat.id == PersonaMessage.chat_id).where(
                    PersonaMessage.id == target_id
                )
            ).scalar_one_or_none()
            owner_id = item.chat.user_id if item and item.chat else None
            return DeletionService._require_owner(item, "PersonaMessage", target_id, owner_id, user_id)

        if target_type == DeletionTargetType.PHOTO_MEMORY:
            item = db.execute(select(PhotoMemory).where(PhotoMemory.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "PhotoMemory", target_id, item.user_id if item else None, user_id)

        if target_type == DeletionTargetType.STORYBOOK:
            item = db.execute(select(StoryBook).where(StoryBook.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "StoryBook", target_id, item.user_id if item else None, user_id)

        if target_type == DeletionTargetType.SHARE_LINK:
            item = db.execute(select(ShareLink).where(ShareLink.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "ShareLink", target_id, item.owner_id if item else None, user_id)

        if target_type == DeletionTargetType.MEMORY_GROUP:
            item = db.execute(select(MemoryGroup).where(MemoryGroup.id == target_id)).scalar_one_or_none()
            return DeletionService._require_owner(item, "MemoryGroup", target_id, item.owner_id if item else None, user_id)

        if target_type == DeletionTargetType.ACCOUNT:
            if target_id != user_id:
                raise ForbiddenException("You can only request deletion of your own account")
            return None

        raise NotFoundException("Deletion target", target_id)

    @staticmethod
    def _require_owner(item, resource: str, resource_id: int, owner_id: int | None, user_id: int):
        if not item:
            raise NotFoundException(resource, resource_id)
        if owner_id != user_id:
            raise ForbiddenException(f"You don't have permission to delete this {resource}")
        return item

    @staticmethod
    def _process_deletion(db: Session, user_id: int, target_type: DeletionTargetType, target_id: int) -> None:
        item = DeletionService._resolve_owned_target(db, user_id, target_type, target_id)
        now = DeletionService._now()

        if target_type == DeletionTargetType.TARGET:
            item.is_deleted = True

        elif target_type == DeletionTargetType.TARGET_MEDIA:
            DeletionService._delete_file_if_exists(item.file_path)
            item.is_deleted = True

        elif target_type == DeletionTargetType.PERSONA:
            item.is_deleted = True
            if item.voice_profile:
                item.voice_profile.is_deleted = True

        elif target_type == DeletionTargetType.PERSONA_CHAT:
            item.deleted_at = now
            messages = db.execute(
                select(PersonaMessage).where(PersonaMessage.chat_id == item.id, PersonaMessage.deleted_at.is_(None))
            ).scalars().all()
            for message in messages:
                message.deleted_at = now

        elif target_type == DeletionTargetType.PERSONA_MESSAGE:
            item.deleted_at = now

        elif target_type == DeletionTargetType.PHOTO_MEMORY:
            DeletionService._delete_file_if_exists(item.file_path)
            item.deleted_at = now

        elif target_type == DeletionTargetType.STORYBOOK:
            item.deleted_at = now
            chapters = db.execute(
                select(StoryChapter).where(StoryChapter.storybook_id == item.id, StoryChapter.deleted_at.is_(None))
            ).scalars().all()
            for chapter in chapters:
                chapter.deleted_at = now

        elif target_type == DeletionTargetType.SHARE_LINK:
            item.is_active = False
            item.disabled_at = now

        elif target_type == DeletionTargetType.MEMORY_GROUP:
            item.deleted_at = now
            members = db.execute(
                select(GroupMember).where(GroupMember.group_id == item.id, GroupMember.deleted_at.is_(None))
            ).scalars().all()
            for member in members:
                member.deleted_at = now
            group_storybooks = db.execute(
                select(GroupStoryBook).where(GroupStoryBook.group_id == item.id, GroupStoryBook.deleted_at.is_(None))
            ).scalars().all()
            for group_storybook in group_storybooks:
                group_storybook.deleted_at = now

        elif target_type == DeletionTargetType.ACCOUNT:
            # TODO: Account 삭제 정책 확정 후 사용자 계정/연관 데이터 삭제 처리 구현
            pass

        db.flush()


deletion_service = DeletionService()
