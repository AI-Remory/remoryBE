from typing import Optional
from pydantic import BaseModel
from app.schemas.common import TimestampMixin
from app.models.interview import InterviewType


class AIInterviewSessionCreateRequest(BaseModel):
    """AI Interview Session 생성 요청"""
    target_id: Optional[int] = None
    photo_memory_id: Optional[int] = None
    interview_type: InterviewType


class AIInterviewSessionSubmitRequest(BaseModel):
    """답변 제출 요청"""
    user_answer: str
    follow_up_question: Optional[str] = None


class AIInterviewSessionResponse(TimestampMixin):
    """AI Interview Session 응답"""
    id: int
    user_id: int
    target_id: Optional[int]
    photo_memory_id: Optional[int]
    interview_type: InterviewType
    current_question: Optional[str]
    user_answer: Optional[str]
    follow_up_question: Optional[str]
    is_completed: bool

    class Config:
        from_attributes = True

