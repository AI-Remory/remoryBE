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


ai_service = AIService()
