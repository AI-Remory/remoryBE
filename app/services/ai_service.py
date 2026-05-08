"""AI Mock 서비스 (프로덕션에서는 실제 API 호출로 교체)"""


class AIService:
    """AI 기능을 담당하는 서비스"""

    @staticmethod
    async def generate_persona_profile(
        target_name: str,
        description: str,
        media_count: int = 0,
    ) -> dict:
        """페르소나 프로필 생성 (Mock)"""
        # 실제로는 OpenAI API를 호출하여 요약 정보를 생성
        return {
            "personality_summary": f"{target_name}은 따뜻한 마음씨를 가진 사람입니다.",
            "speaking_style": "친근하고 정중한 말씨",
            "values_beliefs": "가족을 소중히 여기고 항상 긍정적인 자세를 유지합니다.",
            "memorable_episodes": "평생 많은 추억들을 만들어온 사람입니다.",
        }

    @staticmethod
    async def generate_interview_question(
        interview_type: str,
        context: dict = None,
    ) -> str:
        """인터뷰 질문 생성 (Mock)"""
        # 실제로는 OpenAI API를 호출하여 질문 생성
        questions = {
            "target_profile": "이 사람과 함께 있을 때 가장 기억에 남는 순간은 언제인가요?",
            "photo_memory": "이 사진에 담긴 이야기를 들려주시겠어요?",
            "persona_creation": "이 사람의 가장 큰 장점은 무엇이라고 생각하세요?",
        }
        return questions.get(interview_type, "질문을 생성해주세요.")

    @staticmethod
    async def generate_follow_up_question(
        user_answer: str,
        context: dict = None,
    ) -> str:
        """꼬리 질문 생성 (Mock)"""
        # 실제로는 OpenAI API를 호출하여 꼬리 질문 생성
        return f"그렇군요! {user_answer[:20]}... 에 대해 조금 더 자세히 말씀해 주실 수 있을까요?"

    @staticmethod
    async def generate_storybook(
        target_name: str,
        chapters_data: list,
    ) -> dict:
        """스토리북 생성 (Mock)"""
        # 실제로는 OpenAI API를 호출하여 스토리북 혹은 챕터 생성
        return {
            "chapters": [
                {
                    "order": 1,
                    "title": "만남",
                    "content": f"{target_name}과의 첫 만남은 정말 특별했습니다...",
                    "summary": "첫 만남 이야기",
                }
            ],
            "cover_suggestion": f"{target_name}의 이야기",
        }

    @staticmethod
    async def generate_persona_response(
        user_message: str,
        persona_profile: dict,
    ) -> str:
        """페르소나 응답 생성 (Mock)"""
        # 실제로는 OpenAI API를 호출하여 페르소나 응답 생성
        return f"네, 맞습니다. {user_message[:10]}... 에 대해 이야기해볼까요?"


ai_service = AIService()

