"""Persona chat API."""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    PersonaChatCreateRequest,
    PersonaChatResponse,
    PersonaMessageCreateRequest,
    PersonaMessagePairResponse,
    PersonaMessageResponse,
)
from app.services.chat_service import chat_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["chat"])


@router.post(
    "/personas/{persona_id}/chats",
    response_model=PersonaChatResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_persona_chat(
    persona_id: int,
    chat_data: PersonaChatCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a chat for a persona owned by the current user."""
    try:
        return chat_service.create_chat(db, current_user.id, persona_id, chat_data)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/personas/{persona_id}/chats", response_model=list[PersonaChatResponse])
async def list_persona_chats(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List current user's chats for a persona."""
    try:
        return chat_service.list_chats(db, current_user.id, persona_id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.post(
    "/chats/{chat_id}/messages",
    response_model=PersonaMessagePairResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_message(
    chat_id: int,
    message_data: PersonaMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a user message and mock persona reply."""
    try:
        user_message, persona_message = await chat_service.create_message_pair(
            db=db,
            user_id=current_user.id,
            chat_id=chat_id,
            message_data=message_data,
        )
        return PersonaMessagePairResponse(
            user_message=user_message,
            persona_message=persona_message,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.post(
    "/chats/{chat_id}/audio",
    response_model=PersonaMessagePairResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_audio_message(
    chat_id: int,
    file: UploadFile = File(...),
    generate_audio: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a user audio message, transcribe it, and create a persona reply."""
    try:
        user_message, persona_message = await chat_service.create_audio_message_pair(
            db=db,
            user_id=current_user.id,
            chat_id=chat_id,
            upload_file=file,
            generate_audio=generate_audio,
        )
        return PersonaMessagePairResponse(
            user_message=user_message,
            persona_message=persona_message,
        )
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/chats/{chat_id}/messages", response_model=list[PersonaMessageResponse])
async def list_chat_messages(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List chat messages in created_at ascending order."""
    try:
        return chat_service.list_messages(db, current_user.id, chat_id)
    except RemoryException as e:
        raise to_http_exception(e)
