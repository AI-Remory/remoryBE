"""Schemas for rate limiting and usage limits."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UsageLimitResponse(BaseModel):
    """User monthly usage limit response."""

    id: int
    user_id: int
    period_ym: str

    # Voice generation
    voice_generation_count: int
    voice_generation_limit: int
    voice_generation_remaining: int

    # STT
    stt_request_count: int
    stt_request_limit: int
    stt_request_remaining: int

    # Voice calls
    voice_call_seconds: int
    voice_call_seconds_limit: int
    voice_call_seconds_remaining: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonaUsageLimitResponse(BaseModel):
    """Persona monthly usage limit response."""

    id: int
    persona_id: int
    period_ym: str

    # Voice generation
    voice_generation_count: int
    voice_generation_limit: int
    voice_generation_remaining: int

    # Voice calls
    voice_call_seconds: int
    voice_call_seconds_limit: int
    voice_call_seconds_remaining: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RateLimitEventResponse(BaseModel):
    """Rate limit event response."""

    id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    endpoint: str
    event_type: str
    count: int
    window_seconds: Optional[int] = None
    blocked: bool
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UpdateUsageLimitRequest(BaseModel):
    """Request to update usage limit."""

    voice_generation_limit: Optional[int] = None
    stt_request_limit: Optional[int] = None
    voice_call_seconds_limit: Optional[int] = None


class UpdatePersonaUsageLimitRequest(BaseModel):
    """Request to update persona usage limit."""

    voice_generation_limit: Optional[int] = None
    voice_call_seconds_limit: Optional[int] = None

