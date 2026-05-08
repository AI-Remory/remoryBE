"""v1 API 라우터"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, group, interview, media, persona, photo_memory, sharing, storybook, target

api_v1_router = APIRouter(prefix="/v1")

# 엔드포인트 포함
api_v1_router.include_router(auth.router)
api_v1_router.include_router(target.router)
api_v1_router.include_router(media.router)
api_v1_router.include_router(persona.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(interview.router)
api_v1_router.include_router(photo_memory.router)
api_v1_router.include_router(storybook.router)
api_v1_router.include_router(sharing.router)
api_v1_router.include_router(group.router)

# 다른 엔드포인트들은 나중에 추가할 것
# api_v1_router.include_router(consent.router)

