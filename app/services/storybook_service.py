"""StoryBook business logic."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from app.models.interview import AIInterviewAnswer, AIInterviewQuestion, AIInterviewSession, InterviewType, PhotoMemory
from app.models.storybook import (
    StoryBook,
    StoryBookSourceType,
    StoryBookStatus,
    StoryChapter,
)
from app.schemas.storybook import StoryBookCreateRequest
from app.services.ai import get_llm_service
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException


class StoryBookService:
    """Storybook creation, lookup, chapter listing, and regeneration service."""

    @staticmethod
    def _get_owned_photo_memory(db: Session, user_id: int, photo_memory_id: int) -> PhotoMemory:
        photo_memory = db.execute(
            select(PhotoMemory).where(
                PhotoMemory.id == photo_memory_id,
                PhotoMemory.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not photo_memory:
            raise NotFoundException("PhotoMemory", photo_memory_id)
        if photo_memory.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this photo memory")
        return photo_memory

    @staticmethod
    def _get_owned_interview_session(db: Session, user_id: int, session_id: int) -> AIInterviewSession:
        session = db.execute(
            select(AIInterviewSession)
            .options(
                selectinload(AIInterviewSession.questions).selectinload(AIInterviewQuestion.answers),
                with_loader_criteria(AIInterviewAnswer, AIInterviewAnswer.deleted_at.is_(None)),
            )
            .where(
                AIInterviewSession.id == session_id,
                AIInterviewSession.deleted_at.is_(None),
            )
        ).scalar_one_or_none()
        if not session:
            raise NotFoundException("AIInterviewSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this interview session")
        return session

    @staticmethod
    def _get_owned_storybook(db: Session, user_id: int, storybook_id: int, include_chapters: bool = False) -> StoryBook:
        query = select(StoryBook).where(
            StoryBook.id == storybook_id,
            StoryBook.deleted_at.is_(None),
        )
        if include_chapters:
            query = query.options(
                selectinload(StoryBook.chapters),
                with_loader_criteria(StoryChapter, StoryChapter.deleted_at.is_(None)),
            )

        storybook = db.execute(query).scalar_one_or_none()
        if not storybook:
            raise NotFoundException("StoryBook", storybook_id)
        if storybook.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this storybook")
        return storybook

    @staticmethod
    def _source_type(
        interview_session: AIInterviewSession | None,
        photo_memory: PhotoMemory | None,
    ) -> StoryBookSourceType:
        if interview_session and interview_session.session_type == InterviewType.SELF_STORY:
            return StoryBookSourceType.SELF_STORY
        if interview_session:
            return StoryBookSourceType.INTERVIEW
        if photo_memory:
            return StoryBookSourceType.PHOTO_MEMORY
        raise ValidationException("interview_session_id or photo_memory_id is required")

    @staticmethod
    def _interview_items(interview_session: AIInterviewSession | None) -> list[dict]:
        if not interview_session:
            return []

        items = []
        for question in sorted(interview_session.questions, key=lambda q: (q.order_index, q.id)):
            answers = [
                answer.answer_text or answer.answer_audio_path
                for answer in sorted(question.answers, key=lambda a: (a.created_at, a.id))
                if answer.deleted_at is None
            ]
            items.append(
                {
                    "question_text": question.question_text,
                    "answers": answers,
                }
            )
        return items

    @staticmethod
    def _source_context(photo_memory: PhotoMemory | None) -> dict:
        if not photo_memory:
            return {}
        return {
            "photo_title": photo_memory.title,
            "photo_description": photo_memory.description,
            "file_path": photo_memory.file_path,
            "location": photo_memory.location,
            "taken_at": photo_memory.taken_at.isoformat() if photo_memory.taken_at else None,
        }

    @staticmethod
    def _replace_chapters(db: Session, storybook: StoryBook, chapters: list[dict]) -> None:
        now = datetime.now(UTC)
        for chapter in storybook.chapters:
            if chapter.deleted_at is None:
                chapter.deleted_at = now

        for index, chapter_data in enumerate(chapters, start=1):
            db.add(
                StoryChapter(
                    storybook_id=storybook.id,
                    title=chapter_data.get("title") or f"Chapter {index}",
                    content=chapter_data.get("content") or "",
                    summary=chapter_data.get("summary"),
                    order_index=chapter_data.get("order_index") or index,
                )
            )

    @staticmethod
    async def create_storybook(
        db: Session,
        user_id: int,
        storybook_data: StoryBookCreateRequest,
    ) -> StoryBook:
        if storybook_data.interview_session_id is None and storybook_data.photo_memory_id is None:
            raise ValidationException("interview_session_id or photo_memory_id is required")

        interview_session = None
        photo_memory = None
        if storybook_data.interview_session_id is not None:
            interview_session = StoryBookService._get_owned_interview_session(
                db, user_id, storybook_data.interview_session_id
            )
        if storybook_data.photo_memory_id is not None:
            photo_memory = StoryBookService._get_owned_photo_memory(db, user_id, storybook_data.photo_memory_id)

        source_type = StoryBookService._source_type(interview_session, photo_memory)
        generated = await get_llm_service().generate_storybook(
            title=storybook_data.title,
            interview_questions_answers=StoryBookService._interview_items(interview_session),
            photo_memory=StoryBookService._source_context(photo_memory),
        )

        storybook = StoryBook(
            user_id=user_id,
            photo_memory_id=storybook_data.photo_memory_id,
            interview_session_id=storybook_data.interview_session_id,
            title=storybook_data.title,
            summary=generated["summary"],
            source_type=source_type,
            status=StoryBookStatus.GENERATED,
            visibility=storybook_data.visibility,
        )
        db.add(storybook)
        db.flush()
        StoryBookService._replace_chapters(db, storybook, generated["chapters"])
        db.commit()
        db.refresh(storybook)
        return StoryBookService.get_storybook(db, user_id, storybook.id)

    @staticmethod
    def list_storybooks(db: Session, user_id: int) -> list[StoryBook]:
        return db.execute(
            select(StoryBook)
            .where(
                StoryBook.user_id == user_id,
                StoryBook.deleted_at.is_(None),
            )
            .order_by(StoryBook.created_at.desc(), StoryBook.id.desc())
        ).scalars().all()

    @staticmethod
    def get_storybook(db: Session, user_id: int, storybook_id: int) -> StoryBook:
        return StoryBookService._get_owned_storybook(db, user_id, storybook_id, include_chapters=True)

    @staticmethod
    def list_chapters(db: Session, user_id: int, storybook_id: int) -> list[StoryChapter]:
        StoryBookService._get_owned_storybook(db, user_id, storybook_id)
        return db.execute(
            select(StoryChapter)
            .where(
                StoryChapter.storybook_id == storybook_id,
                StoryChapter.deleted_at.is_(None),
            )
            .order_by(StoryChapter.order_index.asc(), StoryChapter.id.asc())
        ).scalars().all()

    @staticmethod
    async def regenerate_storybook(db: Session, user_id: int, storybook_id: int) -> StoryBook:
        storybook = StoryBookService._get_owned_storybook(db, user_id, storybook_id, include_chapters=True)
        interview_session = None
        photo_memory = None
        if storybook.interview_session_id is not None:
            interview_session = StoryBookService._get_owned_interview_session(
                db, user_id, storybook.interview_session_id
            )
        if storybook.photo_memory_id is not None:
            photo_memory = StoryBookService._get_owned_photo_memory(db, user_id, storybook.photo_memory_id)

        generated = await get_llm_service().generate_storybook(
            title=storybook.title,
            interview_questions_answers=StoryBookService._interview_items(interview_session),
            photo_memory=StoryBookService._source_context(photo_memory),
        )
        storybook.summary = generated["summary"]
        storybook.status = StoryBookStatus.GENERATED
        StoryBookService._replace_chapters(db, storybook, generated["chapters"])
        db.commit()
        return StoryBookService.get_storybook(db, user_id, storybook_id)


storybook_service = StoryBookService()
