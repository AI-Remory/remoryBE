"""Tests for rate limiting and usage limits."""

from app.models.usage_limit import UsageLimit, PersonaUsageLimit, RateLimitEvent
from app.services.rate_limit_service import RateLimitService
from tests.conftest import TestingSessionLocal


def test_user_voice_generation_limit_created_on_first_check(auth_headers, client):
    """Test that usage limit is created on first check."""
    db = TestingSessionLocal()
    try:
        # Get current user
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        # Check voice generation limit
        usage_limit = RateLimitService.get_user_usage_limit(db, user_id)
        assert usage_limit is not None
        assert usage_limit.user_id == user_id
        assert usage_limit.voice_generation_count == 0
        assert usage_limit.voice_generation_limit > 0
    finally:
        db.close()


def test_increment_voice_generation(auth_headers, client):
    """Test incrementing voice generation counter."""
    db = TestingSessionLocal()
    try:
        # Get current user
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        # Get initial usage
        usage_limit_before = RateLimitService.get_user_usage_limit(db, user_id)
        count_before = usage_limit_before.voice_generation_count

        # Increment
        RateLimitService.increment_voice_generation(db, user_id)

        # Check
        usage_limit_after = RateLimitService.get_user_usage_limit(db, user_id)
        assert usage_limit_after.voice_generation_count == count_before + 1
    finally:
        db.close()


def test_increment_stt_counter(auth_headers, client):
    """Test incrementing STT request counter."""
    db = TestingSessionLocal()
    try:
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        usage_limit_before = RateLimitService.get_user_usage_limit(db, user_id)
        count_before = usage_limit_before.stt_request_count

        RateLimitService.increment_stt(db, user_id)

        usage_limit_after = RateLimitService.get_user_usage_limit(db, user_id)
        assert usage_limit_after.stt_request_count == count_before + 1
    finally:
        db.close()


def test_rate_limit_event_recording(auth_headers, client):
    """Test recording rate limit events."""
    db = TestingSessionLocal()
    try:
        user_response = client.get("/api/v1/auth/me", headers=auth_headers)
        user_id = user_response.json()["id"]

        event = RateLimitService.record_rate_limit_event(
            db,
            user_id=user_id,
            ip_address="127.0.0.1",
            endpoint="/api/v1/chats/1/messages",
            event_type="voice_generation",
            blocked=True,
            reason="Monthly limit exceeded",
            window_seconds=60,
        )

        assert event.user_id == user_id
        assert event.endpoint == "/api/v1/chats/1/messages"
        assert event.event_type == "voice_generation"
        assert event.blocked == True
        assert event.reason == "Monthly limit exceeded"
    finally:
        db.close()


def test_admin_can_list_usage_limits(admin_token, client):
    """Test that admin can list usage limits."""
    response = client.get(
        "/api/v1/admin/usage-limits",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_admin_can_list_rate_limit_events(admin_token, client):
    """Test that admin can list rate limit events."""
    response = client.get(
        "/api/v1/admin/rate-limit-events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_general_user_cannot_access_usage_limits(auth_headers, client):
    """Test that general users cannot access usage limits."""
    response = client.get(
        "/api/v1/admin/usage-limits",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_general_user_cannot_access_rate_limit_events(auth_headers, client):
    """Test that general users cannot access rate limit events."""
    response = client.get(
        "/api/v1/admin/rate-limit-events",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_admin_can_update_user_usage_limit(admin_token, auth_headers, client):
    """Test that admin can update user usage limits."""
    # Get user ID
    user_response = client.get("/api/v1/auth/me", headers=auth_headers)
    user_id = user_response.json()["id"]

    # Update limit
    response = client.patch(
        f"/api/v1/admin/users/{user_id}/usage-limit",
        json={"voice_generation_limit": 500},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["voice_generation_limit"] == 500


def test_persona_usage_limit_increments(admin_token, auth_headers, created_persona, client):
    """Test persona usage limit increments."""
    db = TestingSessionLocal()
    try:
        persona_id = created_persona["id"]

        # Get initial
        usage_before = RateLimitService.get_persona_usage_limit(db, persona_id)
        count_before = usage_before.voice_generation_count

        # Increment
        RateLimitService.increment_voice_generation(db, user_id=1, persona_id=persona_id)

        # Check
        usage_after = RateLimitService.get_persona_usage_limit(db, persona_id)
        assert usage_after.voice_generation_count == count_before + 1
    finally:
        db.close()

