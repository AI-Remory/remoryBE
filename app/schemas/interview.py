from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.interview import InterviewStatus, InterviewType
from app.schemas.common import TimestampMixin


class AIInterviewSessionCreateRequest(BaseModel):
    session_type: InterviewType
    title: Optional[str] = Field(default=None, max_length=255)
    target_id: Optional[int] = None
    photo_memory_id: Optional[int] = None


class AIInterviewQuestionCreateRequest(BaseModel):
    question_type: Optional[str] = Field(default=None, max_length=100)


class AIInterviewAnswerCreateRequest(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_audio_path: Optional[str] = None


class AIInterviewAnswerResponse(TimestampMixin):
    id: int
    session_id: int
    question_id: int
    answer_text: Optional[str]
    answer_audio_path: Optional[str]
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AIInterviewQuestionResponse(BaseModel):
    id: int
    session_id: int
    question_text: str
    question_type: Optional[str]
    order_index: int
    created_at: datetime
    answers: list[AIInterviewAnswerResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AIInterviewSessionResponse(TimestampMixin):
    id: int
    user_id: int
    target_id: Optional[int]
    photo_memory_id: Optional[int]
    session_type: InterviewType
    title: Optional[str]
    status: InterviewStatus
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AIInterviewSessionDetailResponse(AIInterviewSessionResponse):
    questions: list[AIInterviewQuestionResponse] = Field(default_factory=list)
