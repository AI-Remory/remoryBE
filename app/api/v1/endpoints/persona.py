"""Persona API."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.persona import PersonaDetailResponse, PersonaStatusResponse
from app.services.persona_service import persona_service
from app.utils.exceptions import RemoryException, to_http_exception

router = APIRouter(tags=["persona"])


@router.post(
    "/targets/{target_id}/persona",
    response_model=PersonaDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_persona(
    target_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a persona for a target owned by the current user."""
    try:
        return await persona_service.create_persona(db, target_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/personas/{persona_id}", response_model=PersonaDetailResponse)
async def get_persona(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a persona owned by the current user."""
    try:
        return persona_service.get_persona(db, persona_id, current_user.id)
    except RemoryException as e:
        raise to_http_exception(e)


@router.get("/personas/{persona_id}/status", response_model=PersonaStatusResponse)
async def get_persona_status(
    persona_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get persona generation status."""
    try:
        persona = persona_service.get_persona_status(db, persona_id, current_user.id)
        return PersonaStatusResponse(
            persona_id=persona.id,
            target_id=persona.target_id,
            status=persona.status,
        )
    except RemoryException as e:
        raise to_http_exception(e)
