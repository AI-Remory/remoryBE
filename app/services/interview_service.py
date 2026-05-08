"""AI interview business logic."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload, with_loader_criteria

from app.models.interview import (
    AIInterviewAnswer,
    AIInterviewQuestion,
    AIInterviewSession,
    InterviewStatus,
    InterviewType,
    PhotoMemory,
)
from app.models.target import Target
from app.schemas.interview import (
    AIInterviewAnswerCreateRequest,
    AIInterviewQuestionCreateRequest,
    AIInterviewSessionCreateRequest,
)
from app.services.ai_service import ai_service
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException


class InterviewService:
    """AI interview session, question, and answer service."""

    @staticmethod
    def _validate_owned_target(db: Session, target_id: int, user_id: int) -> None:
        target = db.execute(
            select(Target).where(
                Target.id == target_id,
                Target.is_deleted == False,
            )
        ).scalar_one_or_none()
        if not target:
            raise NotFoundException("Target", target_id)
        if target.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this target")

    @staticmethod
    def _validate_owned_photo_memory(db: Session, photo_memory_id: int, user_id: int) -> None:
        photo_memory = db.execute(
            select(PhotoMemory).where(
                PhotoMemory.id == photo_memory_id,
                PhotoMemory.is_deleted == False,
            )
        ).scalar_one_or_none()
        if not photo_memory:
            raise NotFoundException("PhotoMemory", photo_memory_id)
        if photo_memory.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this photo memory")

    @staticmethod
    def _get_owned_session(db: Session, session_id: int, user_id: int, include_detail: bool = False) -> AIInterviewSession:
        query = select(AIInterviewSession).where(
            AIInterviewSession.id == session_id,
            AIInterviewSession.deleted_at.is_(None),
        )
        if include_detail:
            query = query.options(
                selectinload(AIInterviewSession.questions).selectinload(AIInterviewQuestion.answers),
                with_loader_criteria(AIInterviewAnswer, AIInterviewAnswer.deleted_at.is_(None)),
            )

        session = db.execute(query).scalar_one_or_none()
        if not session:
            raise NotFoundException("AIInterviewSession", session_id)
        if session.user_id != user_id:
            raise ForbiddenException("You don't have permission to access this interview session")
        return session

    @staticmethod
    def create_session(
        db: Session,
        user_id: int,
        session_data: AIInterviewSessionCreateRequest,
    ) -> AIInterviewSession:
        if session_data.session_type == InterviewType.TARGET_PROFILE:
            if session_data.target_id is None:
                raise ValidationException("target_id is required for TARGET_PROFILE interviews")
            InterviewService._validate_owned_target(db, session_data.target_id, user_id)

        if session_data.session_type == InterviewType.PHOTO_MEMORY:
            # TODO: PhotoMemory 구현 완료 후 photo_memory_id 필수 여부 및 소유권 검사 정책 확정
            if session_data.photo_memory_id is not None:
                InterviewService._validate_owned_photo_memory(db, session_data.photo_memory_id, user_id)

        if session_data.session_type == InterviewType.SELF_STORY and session_data.target_id is not None:
            raise ValidationException("SELF_STORY interviews must not include target_id")

        session = AIInterviewSession(
            user_id=user_id,
            target_id=session_data.target_id,
            photo_memory_id=session_data.photo_memory_id,
            session_type=session_data.session_type,
            title=session_data.title,
            status=InterviewStatus.IN_PROGRESS,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session_detail(db: Session, user_id: int, session_id: int) -> AIInterviewSession:
        return InterviewService._get_owned_session(db, session_id, user_id, include_detail=True)

    @staticmethod
    async def create_question(
        db: Session,
        user_id: int,
        session_id: int,
        question_data: AIInterviewQuestionCreateRequest,
    ) -> AIInterviewQuestion:
        session = InterviewService._get_owned_session(db, session_id, user_id)
        next_order_index = (
            db.execute(
                select(func.count(AIInterviewQuestion.id)).where(
                    AIInterviewQuestion.session_id == session_id,
                )
            ).scalar()
            or 0
        ) + 1

        question_text = await ai_service.generate_mock_interview_question(
            session_type=session.session_type.value,
            order_index=next_order_index,
            context={
                "target_id": session.target_id,
                "photo_memory_id": session.photo_memory_id,
            },
        )
        question = AIInterviewQuestion(
            session_id=session_id,
            question_text=question_text,
            question_type=question_data.question_type,
            order_index=next_order_index,
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def create_answer(
        db: Session,
        user_id: int,
        session_id: int,
        answer_data: AIInterviewAnswerCreateRequest,
    ) -> AIInterviewAnswer:
        InterviewService._get_owned_session(db, session_id, user_id)

        if not answer_data.answer_text and not answer_data.answer_audio_path:
            raise ValidationException("answer_text or answer_audio_path is required")

        question = db.execute(
            select(AIInterviewQuestion).where(
                AIInterviewQuestion.id == answer_data.question_id,
                AIInterviewQuestion.session_id == session_id,
            )
        ).scalar_one_or_none()
        if not question:
            raise NotFoundException("AIInterviewQuestion", answer_data.question_id)

        answer = AIInterviewAnswer(
            session_id=session_id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            answer_audio_path=answer_data.answer_audio_path,
        )
        db.add(answer)
        db.commit()
        db.refresh(answer)
        return answer


interview_service = InterviewService()
