"""LLM service interface, Gemini implementation, and mock fallback."""

from __future__ import annotations

import asyncio
import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

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
    """Deterministic mock LLM used in test env and as fallback."""

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
                "What words did this person often use?",
                "How would you describe this person in one sentence?",
                "What did this person usually say in difficult moments?",
                "What is one memory that shows this person's character well?",
            ],
            "PHOTO_MEMORY": [
                "When was this photo taken, and what was happening around that time?",
                "Who appears in this photo, and what was your relationship with them?",
                "What feeling do you remember most clearly from this day?",
            ],
            "SELF_STORY": [
                "What is one day from your life that you still remember clearly?",
                "What story would you like your family or friends to remember?",
                "What important event helped shape who you are today?",
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
                    answer_text = (
                        "This question has not been answered yet, but it remains an "
                        "important part of the memory record."
                    )
                chapters.append(
                    {
                        "title": f"Chapter {index}: {question[:40]}",
                        "content": f"{question}\n\n{answer_text}",
                        "summary": answer_text[:120],
                        "order_index": index,
                    }
                )
        else:
            photo_title = photo_memory.get("photo_title") or title
            photo_description = (
                photo_memory.get("photo_description")
                or "This storybook was created around the remembered moment in the photo."
            )
            chapters.append(
                {
                    "title": f"Chapter 1: {photo_title}",
                    "content": photo_description,
                    "summary": photo_description[:120],
                    "order_index": 1,
                }
            )

        source_label = "interview" if interview_questions_answers else "photo memory"
        summary = (
            f"'{title}' is a storybook generated from {source_label} material. "
            f"It contains {len(chapters)} chapter(s)."
        )
        return {"summary": summary, "chapters": chapters}


class GeminiLLMService(LLMService):
    """Gemini-backed LLM service with safe mock fallback."""

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self._mock = MockLLMService()
        try:
            from google import genai

            self._client = genai.Client(api_key=api_key)
        except Exception:
            self._client = None

    async def generate_persona_reply(
        self,
        persona: dict,
        recent_messages: list,
        user_message: str,
    ) -> str:
        prompt = (
            "You are writing a persona chat reply for Remory.\n"
            "Reply in the persona's voice, warmly and naturally.\n"
            "Keep the reply under 120 words.\n"
            "Do not mention that you are an AI.\n\n"
            "Safety: do not provide medical, legal, financial, or other sensitive "
            "professional advice. If asked for such advice, respond supportively and "
            "encourage the user to consult a qualified professional.\n\n"
            f"Persona profile:\n{json.dumps(persona, ensure_ascii=False)}\n\n"
            f"Recent messages:\n{json.dumps(recent_messages[-8:], ensure_ascii=False)}\n\n"
            f"User message:\n{user_message}"
        )
        text = await self._generate_text(prompt, max_output_tokens=220, temperature=0.7)
        if not text:
            return await self._mock.generate_persona_reply(persona, recent_messages, user_message)
        return self._limit_text(text, 700)

    async def generate_interview_question(
        self,
        session_type: str,
        previous_questions: list,
    ) -> str:
        prompt = (
            "Generate one concise interview question for Remory.\n"
            "The question should be empathetic, specific, and easy to answer.\n"
            "Return only the question text. Keep it under 30 words.\n\n"
            f"Session type: {session_type}\n"
            f"Previous questions: {json.dumps(previous_questions[-10:], ensure_ascii=False)}"
        )
        text = await self._generate_text(prompt, max_output_tokens=80, temperature=0.6)
        if not text:
            return await self._mock.generate_interview_question(session_type, previous_questions)
        return self._limit_text(text.strip().splitlines()[0], 220)

    async def generate_storybook(
        self,
        title: str,
        interview_questions_answers: list[dict],
        photo_memory: dict | None = None,
    ) -> dict:
        photo_memory = photo_memory or {}
        prompt = self._storybook_prompt(title, interview_questions_answers, photo_memory)
        text = await self._generate_text(
            prompt,
            max_output_tokens=1600,
            temperature=0.5,
            response_mime_type="application/json",
        )
        if not text:
            return await self._mock.generate_storybook(title, interview_questions_answers, photo_memory)

        parsed = self._parse_json_object(text)
        if not parsed:
            return await self._mock.generate_storybook(title, interview_questions_answers, photo_memory)

        normalized = self._normalize_storybook(parsed)
        if not normalized:
            return await self._mock.generate_storybook(title, interview_questions_answers, photo_memory)
        return normalized

    async def _generate_text(
        self,
        prompt: str,
        *,
        max_output_tokens: int,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str | None:
        if self._client is None:
            return None
        try:
            return await asyncio.to_thread(
                self._generate_text_sync,
                prompt,
                max_output_tokens,
                temperature,
                response_mime_type,
            )
        except Exception:
            return None

    def _generate_text_sync(
        self,
        prompt: str,
        max_output_tokens: int,
        temperature: float,
        response_mime_type: str | None,
    ) -> str | None:
        from google.genai import types

        config_kwargs: dict[str, Any] = {
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        return getattr(response, "text", None)

    @staticmethod
    def _limit_text(value: str, max_chars: int) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) <= max_chars:
            return value
        return value[: max_chars - 3].rstrip() + "..."

    @staticmethod
    def _parse_json_object(value: str) -> dict | None:
        value = value.strip()
        if value.startswith("```"):
            value = re.sub(r"^```(?:json)?\s*", "", value)
            value = re.sub(r"\s*```$", "", value)
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", value, flags=re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return parsed if isinstance(parsed, dict) else None

    @classmethod
    def _normalize_storybook(cls, data: dict) -> dict | None:
        summary = data.get("summary")
        chapters = data.get("chapters")
        if not isinstance(summary, str) or not isinstance(chapters, list) or not chapters:
            return None

        normalized_chapters: list[dict] = []
        for index, chapter in enumerate(chapters[:8], start=1):
            if not isinstance(chapter, dict):
                return None
            title = chapter.get("title")
            content = chapter.get("content")
            if not isinstance(title, str) or not isinstance(content, str):
                return None
            raw_summary = chapter.get("summary")
            chapter_summary = raw_summary if isinstance(raw_summary, str) else content[:120]
            normalized_chapters.append(
                {
                    "title": cls._limit_text(title, 120),
                    "content": cls._limit_text(content, 2400),
                    "summary": cls._limit_text(chapter_summary, 300),
                    "order_index": index,
                }
            )

        return {
            "summary": cls._limit_text(summary, 600),
            "chapters": normalized_chapters,
        }

    @staticmethod
    def _storybook_prompt(
        title: str,
        interview_questions_answers: list[dict],
        photo_memory: dict,
    ) -> str:
        return (
            "Create a Remory storybook from the provided source material.\n"
            "Return valid JSON only. Do not include markdown fences or commentary.\n"
            "The JSON must match this exact shape:\n"
            "{\n"
            '  "summary": "string, max 100 words",\n'
            '  "chapters": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "content": "string, 120-350 words",\n'
            '      "summary": "string, max 40 words",\n'
            '      "order_index": 1\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Create 1 to 5 chapters. Preserve factual details from the source. "
            "Avoid inventing names, dates, or places that are not provided.\n\n"
            f"Storybook title: {title}\n"
            "Interview questions and answers:\n"
            f"{json.dumps(interview_questions_answers, ensure_ascii=False)}\n\n"
            "Photo memory context:\n"
            f"{json.dumps(photo_memory, ensure_ascii=False)}"
        )


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def get_llm_service() -> LLMService:
    """Return the configured LLM service instance."""

    if settings.ENVIRONMENT == "test" or _running_under_pytest():
        return MockLLMService()

    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return MockLLMService()

    service = GeminiLLMService(api_key=api_key, model=settings.GEMINI_MODEL)
    if service._client is None:
        return MockLLMService()
    return service
