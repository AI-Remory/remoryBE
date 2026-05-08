"""AI mock service.

Production integrations can replace these methods with real model/API calls.
"""

from app.models.target import TargetType


class AIService:
    """Service boundary for AI-backed features."""

    @staticmethod
    async def generate_persona_profile(
        target_name: str,
        relationship: TargetType | str,
        description: str | None,
        image_count: int = 0,
        voice_count: int = 0,
    ) -> dict[str, str]:
        """Generate a deterministic persona profile without calling an AI API."""
        relationship_value = relationship.value if isinstance(relationship, TargetType) else str(relationship)
        clean_description = description or "No description was provided."

        persona_name = f"{target_name} Persona"
        speaking_style = (
            f"Speaks warmly and naturally as a {relationship_value}, "
            f"with a tone grounded in the provided memories."
        )
        personality_summary = (
            f"{target_name} is represented as a thoughtful {relationship_value}. "
            f"Profile hints: {clean_description}"
        )
        memory_summary = (
            f"Built from {image_count} uploaded photo(s), {voice_count} uploaded voice sample(s), "
            f"and the target description."
        )
        system_prompt = (
            f"You are {persona_name}. Respond as {target_name}, the user's {relationship_value}. "
            f"Use the following profile: {clean_description}. "
            f"Reference available context from {image_count} photo(s) and {voice_count} voice sample(s)."
        )

        return {
            "persona_name": persona_name,
            "speaking_style": speaking_style,
            "personality_summary": personality_summary,
            "memory_summary": memory_summary,
            "system_prompt": system_prompt,
        }

    @staticmethod
    async def generate_interview_question(
        interview_type: str,
        context: dict | None = None,
    ) -> str:
        """Generate an interview question (mock)."""
        questions = {
            "target_profile": "What memory best captures this person's character?",
            "photo_memory": "What story should this photo preserve?",
            "persona_creation": "What traits should this persona always remember?",
        }
        return questions.get(interview_type, "What memory would you like to preserve?")

    @staticmethod
    async def generate_mock_interview_question(
        session_type: str,
        order_index: int = 1,
        context: dict | None = None,
    ) -> str:
        """Generate a deterministic interview question without calling an AI API."""
        questions = {
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
        options = questions.get(session_type, questions["SELF_STORY"])
        return options[(order_index - 1) % len(options)]

    @staticmethod
    async def generate_follow_up_question(
        user_answer: str,
        context: dict | None = None,
    ) -> str:
        """Generate a follow-up interview question (mock)."""
        return f"Can you share a little more about this memory: {user_answer[:40]}?"

    @staticmethod
    async def generate_storybook(
        target_name: str,
        chapters_data: list,
    ) -> dict:
        """Generate a storybook draft (mock)."""
        return {
            "chapters": [
                {
                    "order": 1,
                    "title": "Beginning",
                    "content": f"This chapter preserves an important memory of {target_name}.",
                    "summary": f"A short memory about {target_name}.",
                }
            ],
            "cover_suggestion": f"A warm portrait-style cover for {target_name}.",
        }

    @staticmethod
    async def generate_persona_response(
        user_message: str,
        persona_profile: dict,
    ) -> str:
        """Generate a persona chat response (mock)."""
        persona_name = persona_profile.get("persona_name", "Persona")
        return f"{persona_name}: I hear you. Tell me more about {user_message[:40]}."

    @staticmethod
    async def generate_mock_persona_reply(
        user_message: str,
        persona_profile: dict,
    ) -> str:
        """Generate a deterministic persona reply without calling an AI API."""
        persona_name = persona_profile.get("persona_name") or "Persona"
        speaking_style = persona_profile.get("speaking_style") or "warm and concise"
        memory_summary = persona_profile.get("memory_summary") or "available memories"
        return (
            f"{persona_name}: I remember this through {memory_summary}. "
            f"Speaking in a {speaking_style} style, I would say: {user_message[:80]}"
        )


ai_service = AIService()
