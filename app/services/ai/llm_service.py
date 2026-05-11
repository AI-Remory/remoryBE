"""LLM service interface and mock implementation."""

from abc import ABC, abstractmethod

from app.core.settings import settings


class LLMService(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate_persona_reply(
        self,
        persona: dict,
        recent_messages: list,
        user_message: str,
    ) -> str: ...

    @abstractmethod
    async def generate_interview_question(
        self,
        session_type: str,
        previous_questions: list,
    ) -> str: ...

    @abstractmethod
    async def generate_storybook(
        self,
        title: str,
        interview_questions_answers: list[dict],
        photo_memory: dict | None = None,
    ) -> dict: ...


class MockLLMService(LLMService):
    """Deterministic mock LLM — used in test env and as fallback."""

    async def generate_persona_reply(
        self,
        persona: dict,
        recent_messages: list,
        user_message: str,
    ) -> str:
        persona_name = persona.get("persona_name", "Persona")
        speaking_style = persona.get("speaking_style", "warm and concise")
        memory_summary = persona.get("memory_summary", "available memories")
        return (
            f"{persona_name}: I remember this through {memory_summary}. "
            f"Speaking in a {speaking_style} style, I would say: {user_message[:80]}"
        )

    async def generate_interview_question(
        self,
        session_type: str,
        previous_questions: list,
    ) -> str:
        questions_map: dict[str, list[str]] = {
            "TARGET_PROFILE": [
                "이 사람이 평소 자주 하던 말은 무엇인가요?",
                "이 사람을 세 단어로 표현하면 무엇인가요?",
                "이 사람이 힘든 상황에서 자주 해주던 말은 무엇인가요?",
                "이 사람과 가장 기억에 남는 에피소드는 무엇인가요?",
            ],
            "PHOTO_MEMORY": [
                "이 사진은 언제 찍은 사진인가요?",
                "사진 속 사람들과는 어떤 관계였나요?",
                "이날 가장 기억나는 감정은 무엇인가요?",
            ],
            "SELF_STORY": [
                "오늘 가장 기억에 남는 일은 무엇인가요?",
                "나중에 가족이나 친구에게 남기고 싶은 말이 있나요?",
                "지금의 나를 만든 중요한 사건은 무엇인가요?",
            ],
        }
        order_index = len(previous_questions) + 1
        options = questions_map.get(session_type, questions_map["SELF_STORY"])
        return options[(order_index - 1) % len(options)]

    async def generate_storybook(
        self,
        title: str,
        interview_questions_answers: list[dict],
        photo_memory: dict | None = None,
    ) -> dict:
        photo_memory = photo_memory or {}
        chapters: list[dict] = []

        if interview_questions_answers:
            for index, item in enumerate(interview_questions_answers, start=1):
                question = item.get("question_text") or "Untitled question"
                answers = item.get("answers") or []
                answer_text = " ".join(a for a in answers if a).strip()
                if not answer_text:
                    answer_text = "아직 답변이 기록되지 않았지만, 이 질문은 중요한 기억의 실마리로 남아 있습니다."
                chapters.append({
                    "title": f"Chapter {index}: {question[:40]}",
                    "content": f"{question}\n\n{answer_text}",
                    "summary": answer_text[:120],
                    "order_index": index,
                })
        else:
            photo_title = photo_memory.get("photo_title") or title
            photo_description = (
                photo_memory.get("photo_description")
                or "사진에 담긴 순간을 중심으로 이야기를 구성했습니다."
            )
            chapters.append({
                "title": f"Chapter 1: {photo_title}",
                "content": photo_description,
                "summary": photo_description[:120],
                "order_index": 1,
            })

        source_label = "인터뷰" if interview_questions_answers else "사진 메모리"
        summary = (
            f"{source_label} 자료를 바탕으로 생성한 '{title}' 스토리북입니다. "
            f"총 {len(chapters)}개의 챕터로 구성되었습니다."
        )
        return {"summary": summary, "chapters": chapters}


def get_llm_service() -> LLMService:
    """Return the appropriate LLM service instance.

    ENVIRONMENT=test → always MockLLMService.
    Step 2 will add GeminiLLMService for development/production.
    """
    if settings.ENVIRONMENT == "test":
        return MockLLMService()
    # Step 2: return GeminiLLMService when GEMINI_API_KEY is set
    return MockLLMService()
