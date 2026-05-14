"""Rate limiting and usage limit service."""

from datetime import UTC, datetime
from typing import Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.usage_limit import UsageLimit, PersonaUsageLimit, RateLimitEvent
from app.utils.exceptions import ForbiddenException


class RateLimitService:
    """Service for rate limiting and usage limit management.

    Currently DB-based, but designed to allow future migration to Redis.
    """

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _get_current_period_ym() -> str:
        """Get current period in YYYY-MM format."""
        now = RateLimitService._now()
        return now.strftime("%Y-%m")

    @staticmethod
    def _get_or_create_user_usage_limit(
        db: Session,
        user_id: int,
        period_ym: Optional[str] = None,
    ) -> UsageLimit:
        """Get or create usage limit record for user in given period."""
        if period_ym is None:
            period_ym = RateLimitService._get_current_period_ym()

        usage_limit = db.execute(
            select(UsageLimit).where(
                and_(
                    UsageLimit.user_id == user_id,
                    UsageLimit.period_ym == period_ym,
                )
            )
        ).scalar_one_or_none()

        if usage_limit is None:
            usage_limit = UsageLimit(
                user_id=user_id,
                period_ym=period_ym,
                voice_generation_count=0,
                voice_generation_limit=settings.MONTHLY_USER_VOICE_GENERATION_LIMIT,
                stt_request_count=0,
                stt_request_limit=settings.MONTHLY_USER_STT_REQUEST_LIMIT,
                voice_call_seconds=0,
                voice_call_seconds_limit=settings.MONTHLY_USER_VOICE_CALL_SECONDS_LIMIT,
            )
            db.add(usage_limit)
            try:
                db.commit()
                db.refresh(usage_limit)
            except IntegrityError:
                # Concurrent create: rollback and load the row created by another request.
                db.rollback()
                usage_limit = db.execute(
                    select(UsageLimit).where(
                        and_(
                            UsageLimit.user_id == user_id,
                            UsageLimit.period_ym == period_ym,
                        )
                    )
                ).scalar_one()
            except SQLAlchemyError:
                db.rollback()
                raise

        return usage_limit

    @staticmethod
    def _get_or_create_persona_usage_limit(
        db: Session,
        persona_id: int,
        period_ym: Optional[str] = None,
    ) -> PersonaUsageLimit:
        """Get or create usage limit record for persona in given period."""
        if period_ym is None:
            period_ym = RateLimitService._get_current_period_ym()

        usage_limit = db.execute(
            select(PersonaUsageLimit).where(
                and_(
                    PersonaUsageLimit.persona_id == persona_id,
                    PersonaUsageLimit.period_ym == period_ym,
                )
            )
        ).scalar_one_or_none()

        if usage_limit is None:
            usage_limit = PersonaUsageLimit(
                persona_id=persona_id,
                period_ym=period_ym,
                voice_generation_count=0,
                voice_generation_limit=settings.MONTHLY_PERSONA_VOICE_GENERATION_LIMIT,
                voice_call_seconds=0,
                voice_call_seconds_limit=settings.MONTHLY_USER_VOICE_CALL_SECONDS_LIMIT,
            )
            db.add(usage_limit)
            try:
                db.commit()
                db.refresh(usage_limit)
            except IntegrityError:
                # Concurrent create: rollback and load the row created by another request.
                db.rollback()
                usage_limit = db.execute(
                    select(PersonaUsageLimit).where(
                        and_(
                            PersonaUsageLimit.persona_id == persona_id,
                            PersonaUsageLimit.period_ym == period_ym,
                        )
                    )
                ).scalar_one()
            except SQLAlchemyError:
                db.rollback()
                raise

        return usage_limit

    @staticmethod
    def check_voice_generation_limit(db: Session, user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if user can generate voice.

        Returns: (allowed, error_message)
        """
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        if usage_limit.voice_generation_count >= usage_limit.voice_generation_limit:
            remaining = usage_limit.voice_generation_limit - usage_limit.voice_generation_count
            return False, f"Monthly voice generation limit exceeded. Limit: {usage_limit.voice_generation_limit}"
        return True, None

    @staticmethod
    def check_persona_voice_generation_limit(db: Session, persona_id: int) -> Tuple[bool, Optional[str]]:
        """Check if persona can generate voice.

        Returns: (allowed, error_message)
        """
        usage_limit = RateLimitService._get_or_create_persona_usage_limit(db, persona_id)
        if usage_limit.voice_generation_count >= usage_limit.voice_generation_limit:
            return False, f"Persona monthly voice generation limit exceeded. Limit: {usage_limit.voice_generation_limit}"
        return True, None

    @staticmethod
    def check_stt_limit(db: Session, user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if user can make STT requests.

        Returns: (allowed, error_message)
        """
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        if usage_limit.stt_request_count >= usage_limit.stt_request_limit:
            return False, f"Monthly STT request limit exceeded. Limit: {usage_limit.stt_request_limit}"
        return True, None

    @staticmethod
    def check_voice_call_limit(
        db: Session,
        user_id: int,
        seconds: int,
    ) -> Tuple[bool, Optional[str]]:
        """Check if user can use voice call for given duration.

        Returns: (allowed, error_message)
        """
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        if usage_limit.voice_call_seconds + seconds > usage_limit.voice_call_seconds_limit:
            remaining = usage_limit.voice_call_seconds_limit - usage_limit.voice_call_seconds
            return False, f"Monthly voice call duration limit exceeded. Remaining: {remaining}s"
        return True, None

    @staticmethod
    def increment_voice_generation(
        db: Session,
        user_id: int,
        persona_id: Optional[int] = None,
    ) -> None:
        """Increment voice generation counters."""
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        usage_limit.voice_generation_count += 1
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

        if persona_id:
            persona_usage = RateLimitService._get_or_create_persona_usage_limit(db, persona_id)
            persona_usage.voice_generation_count += 1
            try:
                db.commit()
            except SQLAlchemyError:
                db.rollback()
                raise

    @staticmethod
    def increment_stt(db: Session, user_id: int) -> None:
        """Increment STT request counter."""
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        usage_limit.stt_request_count += 1
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

    @staticmethod
    def increment_voice_call(
        db: Session,
        user_id: int,
        persona_id: Optional[int],
        seconds: int,
    ) -> None:
        """Increment voice call duration counters."""
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        usage_limit.voice_call_seconds += seconds
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise

        if persona_id:
            persona_usage = RateLimitService._get_or_create_persona_usage_limit(db, persona_id)
            persona_usage.voice_call_seconds += seconds
            try:
                db.commit()
            except SQLAlchemyError:
                db.rollback()
                raise

    @staticmethod
    def record_rate_limit_event(
        db: Session,
        user_id: Optional[int],
        ip_address: Optional[str],
        endpoint: str,
        event_type: str,
        blocked: bool,
        reason: Optional[str] = None,
        window_seconds: Optional[int] = None,
    ) -> RateLimitEvent:
        """Record a rate limit or abuse event."""
        event = RateLimitEvent(
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint,
            event_type=event_type,
            blocked=blocked,
            reason=reason,
            window_seconds=window_seconds,
        )
        db.add(event)
        try:
            db.commit()
            db.refresh(event)
        except SQLAlchemyError:
            db.rollback()
            raise
        return event

    @staticmethod
    def get_user_usage_limit(db: Session, user_id: int) -> UsageLimit:
        """Get user's current usage limit."""
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        return usage_limit

    @staticmethod
    def get_persona_usage_limit(db: Session, persona_id: int) -> PersonaUsageLimit:
        """Get persona's current usage limit."""
        usage_limit = RateLimitService._get_or_create_persona_usage_limit(db, persona_id)
        return usage_limit

    @staticmethod
    def list_user_usage_limits(
        db: Session,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List all user usage limits."""
        if user_id is not None:
            # Existing users may not have the current period row yet.
            RateLimitService._get_or_create_user_usage_limit(db, user_id)

        query = select(UsageLimit)
        count_query = select(func.count(UsageLimit.id))
        if user_id is not None:
            query = query.where(UsageLimit.user_id == user_id)
            count_query = count_query.where(UsageLimit.user_id == user_id)

        query = query.order_by(UsageLimit.created_at.desc())
        total = db.execute(count_query).scalar_one()
        items = db.execute(query.offset(skip).limit(limit)).scalars().all()
        return {"total": int(total), "items": items}

    @staticmethod
    def list_rate_limit_events(
        db: Session,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """List rate limit events."""
        query = select(RateLimitEvent)
        count_query = select(func.count(RateLimitEvent.id))
        if user_id is not None:
            query = query.where(RateLimitEvent.user_id == user_id)
            count_query = count_query.where(RateLimitEvent.user_id == user_id)
        query = query.order_by(RateLimitEvent.created_at.desc())

        total = db.execute(count_query).scalar_one()
        items = db.execute(query.offset(skip).limit(limit)).scalars().all()
        return {"total": int(total), "items": items}

    @staticmethod
    def update_user_usage_limit(
        db: Session,
        user_id: int,
        voice_generation_limit: Optional[int] = None,
        stt_request_limit: Optional[int] = None,
        voice_call_seconds_limit: Optional[int] = None,
    ) -> UsageLimit:
        """Update user's usage limit (admin only)."""
        usage_limit = RateLimitService._get_or_create_user_usage_limit(db, user_id)
        if voice_generation_limit is not None:
            usage_limit.voice_generation_limit = voice_generation_limit
        if stt_request_limit is not None:
            usage_limit.stt_request_limit = stt_request_limit
        if voice_call_seconds_limit is not None:
            usage_limit.voice_call_seconds_limit = voice_call_seconds_limit
        try:
            db.commit()
            db.refresh(usage_limit)
        except SQLAlchemyError:
            db.rollback()
            raise
        return usage_limit

    @staticmethod
    def update_persona_usage_limit(
        db: Session,
        persona_id: int,
        voice_generation_limit: Optional[int] = None,
        voice_call_seconds_limit: Optional[int] = None,
    ) -> PersonaUsageLimit:
        """Update persona's usage limit (admin only)."""
        usage_limit = RateLimitService._get_or_create_persona_usage_limit(db, persona_id)
        if voice_generation_limit is not None:
            usage_limit.voice_generation_limit = voice_generation_limit
        if voice_call_seconds_limit is not None:
            usage_limit.voice_call_seconds_limit = voice_call_seconds_limit
        try:
            db.commit()
            db.refresh(usage_limit)
        except SQLAlchemyError:
            db.rollback()
            raise
        return usage_limit

