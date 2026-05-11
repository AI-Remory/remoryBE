"""v1 API 라우터"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, deletion, group, interview, media, persona, photo_memory, sharing, storybook, target, consent, verification, admin

api_v1_router = APIRouter(prefix="/v1")

# 엔드포인트 포함
api_v1_router.include_router(auth.router)
api_v1_router.include_router(target.router)
api_v1_router.include_router(verification.router)
api_v1_router.include_router(verification.detail_router)
api_v1_router.include_router(media.router)
api_v1_router.include_router(persona.router)
api_v1_router.include_router(chat.router)
api_v1_router.include_router(interview.router)
api_v1_router.include_router(photo_memory.router)
api_v1_router.include_router(storybook.router)
api_v1_router.include_router(sharing.router)
api_v1_router.include_router(group.router)
api_v1_router.include_router(deletion.router)
api_v1_router.include_router(consent.router)
api_v1_router.include_router(admin.router)

