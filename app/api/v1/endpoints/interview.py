"""AI interview API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.interview import (
    AIInterviewAnswerCreateRequest,
    AIInterviewAnswerResponse,
    AIInterviewQuestionCreateRequest,
    AIInterviewQuestionResponse,
    AIInterviewSessionCreateRequest,
    AIInterviewSessionDetailResponse,
    AIInterviewSessionResponse,
)
from app.services.interview_service import interview_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(prefix="/interviews", tags=["interview"])


@router.post("", response_model=AIInterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_interview_session(
    session_data: AIInterviewSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create an AI interview session for the current user."""
    try:
        return interview_service.create_session(db, current_user.id, session_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/{session_id}", response_model=AIInterviewSessionDetailResponse)
async def get_interview_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get an interview session with questions and non-deleted answers."""
    try:
        return interview_service.get_session_detail(db, current_user.id, session_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.post(
    "/{session_id}/questions",
    response_model=AIInterviewQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_question(
    session_id: int,
    question_data: AIInterviewQuestionCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and store the next mock interview question."""
    try:
        return await interview_service.create_question(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            question_data=question_data or AIInterviewQuestionCreateRequest(),
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.post(
    "/{session_id}/answers",
    response_model=AIInterviewAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_answer(
    session_id: int,
    answer_data: AIInterviewAnswerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store an answer for a question in the interview session."""
    try:
        return interview_service.create_answer(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            answer_data=answer_data,
        )
    except RemoryException as e:
        raise to_http_exception(e)
