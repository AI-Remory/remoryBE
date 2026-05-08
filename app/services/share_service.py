"""ShareLink business logic."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from app.models.sharing import ShareLink
from app.models.storybook import StoryBook, StoryBookVisibility, StoryChapter
from app.schemas.sharing import ShareLinkCreateRequest
from app.utils.exceptions import ForbiddenException, NotFoundException


class ShareService:
    """Token share link creation, listing, public lookup, and disable service."""

    @staticmethod
    def _share_url(token: str) -> str:
        return f"/api/v1/share/{token}"

    @staticmethod
    def _get_owned_storybook(db: Session, user_id: int, storybook_id: int) -> StoryBook:
        storybook = db.execute(
            select(StoryBook).where(
                StoryBook.id == storybook_id,
                StoryBook.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not storybook:
            raise NotFoundException("StoryBook", storybook_id)
        if storybook.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this storybook")
        return storybook

    @staticmethod
    def _get_owned_share_link(db: Session, user_id: int, share_link_id: int) -> ShareLink:
        share_link = db.execute(
            select(ShareLink).where(ShareLink.id == share_link_id)
        ).scalar_one_or_none()
        if not share_link:
            raise NotFoundException("ShareLink", share_link_id)
        if share_link.owner_id != user_id:
            raise ForbiddenException("You don't have permission to access this share link")
        return share_link

    @staticmethod
    def _serialize_share_link(share_link: ShareLink) -> dict:
        return {
            "id": share_link.id,
            "storybook_id": share_link.storybook_id,
            "owner_id": share_link.owner_id,
            "token": share_link.token,
            "is_active": share_link.is_active,
            "expires_at": share_link.expires_at,
            "disabled_at": share_link.disabled_at,
            "created_at": share_link.created_at,
            "updated_at": share_link.updated_at,
            "share_url": ShareService._share_url(share_link.token),
        }

    @staticmethod
    def create_share_link(
        db: Session,
        user_id: int,
        storybook_id: int,
        share_data: ShareLinkCreateRequest,
    ) -> dict:
        storybook = ShareService._get_owned_storybook(db, user_id, storybook_id)
        share_link = ShareLink(
            storybook_id=storybook_id,
            owner_id=user_id,
            expires_at=share_data.expires_at,
        )
        storybook.visibility = StoryBookVisibility.LINK
        db.add(share_link)
        db.commit()
        db.refresh(share_link)
        return ShareService._serialize_share_link(share_link)

    @staticmethod
    def list_share_links(db: Session, user_id: int, storybook_id: int) -> list[dict]:
        ShareService._get_owned_storybook(db, user_id, storybook_id)
        share_links = db.execute(
            select(ShareLink)
            .where(ShareLink.storybook_id == storybook_id)
            .order_by(ShareLink.created_at.desc(), ShareLink.id.desc())
        ).scalars().all()
        return [ShareService._serialize_share_link(share_link) for share_link in share_links]

    @staticmethod
    def get_public_storybook(db: Session, token: str) -> dict:
        share_link = db.execute(
            select(ShareLink)
            .options(
                selectinload(ShareLink.storybook).selectinload(StoryBook.chapters),
                with_loader_criteria(StoryChapter, StoryChapter.deleted_at.is_(None)),
            )
            .where(ShareLink.token == token)
        ).scalar_one_or_none()

        if not share_link:
            raise NotFoundException("ShareLink")
        if not share_link.is_active:
            raise ForbiddenException("This share link is disabled")
        if share_link.expires_at is not None:
            expires_at = share_link.expires_at
            now = datetime.now(UTC)
            if expires_at.tzinfo is None:
                now = now.replace(tzinfo=None)
            if expires_at <= now:
                raise ForbiddenException("This share link has expired")

        storybook = share_link.storybook
        if not storybook or storybook.deleted_at is not None:
            raise NotFoundException("StoryBook")

        chapters = [
            {
                "title": chapter.title,
                "content": chapter.content,
                "summary": chapter.summary,
                "order_index": chapter.order_index,
            }
            for chapter in sorted(storybook.chapters, key=lambda item: (item.order_index, item.id))
            if chapter.deleted_at is None
        ]
        return {
            "title": storybook.title,
            "summary": storybook.summary,
            "visibility": storybook.visibility,
            "chapters": chapters,
        }

    @staticmethod
    def disable_share_link(db: Session, user_id: int, share_link_id: int) -> dict:
        share_link = ShareService._get_owned_share_link(db, user_id, share_link_id)
        share_link.is_active = False
        share_link.disabled_at = datetime.now(UTC)
        db.commit()
        db.refresh(share_link)
        return {
            "id": share_link.id,
            "is_active": share_link.is_active,
            "disabled_at": share_link.disabled_at,
        }


share_service = ShareService()
