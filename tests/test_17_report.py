"""Tests for report functionality."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.report import ReportStatus, ReportTargetType, ReportReasonType
from app.models.persona import Persona, PersonaStatus
from app.models.storybook import StoryBook, StoryBookStatus, StoryBookVisibility
from app.models.sharing import ShareLink
from app.models.chat import PersonaMessage, SenderType, MessageType
from app.models.target import Target, TargetType
from app.models.user import UserRole


def test_create_report_success(client: TestClient, db: Session, authorized_user, target_with_persona):
    """Test successful report creation."""
    user = authorized_user
    target, persona = target_with_persona

    response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
            "reason_detail": "This persona contains harmful content",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["target_type"] == "PERSONA"
    assert data["target_id"] == persona.id
    assert data["reason_type"] == "HARMFUL_CONTENT"
    assert data["status"] == "PENDING"
    assert data["reporter_user_id"] == user["user_id"]


def test_list_user_reports(client: TestClient, db: Session, authorized_user, target_with_persona):
    """Test listing user's own reports."""
    user = authorized_user
    target, persona = target_with_persona

    # Create a report
    client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )

    # List reports
    response = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["target_type"] == "PERSONA"


def test_get_user_report(client: TestClient, db: Session, authorized_user, target_with_persona):
    """Test getting a specific user report."""
    user = authorized_user
    target, persona = target_with_persona

    # Create a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Get report
    response = client.get(
        f"/api/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert data["target_type"] == "PERSONA"


def test_user_cannot_view_others_reports(client: TestClient, db: Session, authorized_user, other_authorized_user, target_with_persona):
    """Test that users cannot view others' reports."""
    user1 = authorized_user
    user2 = other_authorized_user
    target, persona = target_with_persona

    # User1 creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user1['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # User2 tries to view it
    response = client.get(
        f"/api/v1/reports/{report_id}",
        headers={"Authorization": f"Bearer {user2['access_token']}"},
    )

    assert response.status_code == 403


def test_admin_list_all_reports(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can list all reports."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )

    # Admin lists reports
    response = client.get(
        "/api/v1/admin/reports",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_admin_get_report(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can get a specific report."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin gets report
    response = client.get(
        f"/api/v1/admin/reports/{report_id}",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert data["reporter_user_id"] == user["user_id"]


def test_admin_mark_report_as_reviewing(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can mark report as reviewing."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin marks as reviewing
    response = client.patch(
        f"/api/v1/admin/reports/{report_id}/reviewing",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"admin_note": "Under review"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REVIEWING"
    assert data["reviewed_by"] == admin["user_id"]


def test_admin_resolve_report(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can resolve report without taking action."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin resolves
    response = client.patch(
        f"/api/v1/admin/reports/{report_id}/resolve",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"admin_note": "No action needed"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"


def test_admin_reject_report(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can reject report."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin rejects
    response = client.patch(
        f"/api/v1/admin/reports/{report_id}/reject",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"admin_note": "False report"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"


def test_admin_take_action_on_persona_report(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test admin can take action on persona report (disable persona)."""
    from app.models.persona import Persona

    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona
    persona_id = persona.id

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona_id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin takes action
    response = client.patch(
        f"/api/v1/admin/reports/{report_id}/action-taken",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
        json={"admin_note": "Persona disabled due to harmful content"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTION_TAKEN"

    # Verify persona is disabled - requery from db
    disabled_persona = db.get(Persona, persona_id)
    assert disabled_persona.disabled_at is not None
    assert "HARMFUL_CONTENT" in disabled_persona.disabled_reason


def test_admin_take_action_on_storybook_report(client: TestClient, db: Session, authorized_user, admin_user, storybook):
    """Test admin can take action on storybook report (disable storybook)."""
    from app.models.storybook import StoryBook

    user = authorized_user
    admin = admin_user
    storybook_id = storybook.id

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "STORYBOOK",
            "target_id": storybook_id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin takes action
    response = client.patch(
        f"/api/v1/admin/reports/{report_id}/action-taken",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACTION_TAKEN"

    # Verify storybook is disabled - requery from db
    disabled_storybook = db.get(StoryBook, storybook_id)
    assert disabled_storybook.disabled_at is not None


def test_audit_log_created_for_report(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test that audit log is created when report is created."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )

    # Admin checks audit logs
    response = client.get(
        "/api/v1/admin/audit-logs?action=REPORT_CREATED",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_audit_log_created_for_report_action(client: TestClient, db: Session, authorized_user, admin_user, target_with_persona):
    """Test that audit log is created when admin takes action on report."""
    user = authorized_user
    admin = admin_user
    target, persona = target_with_persona

    # User creates a report
    create_response = client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user['access_token']}"},
        json={
            "target_type": "PERSONA",
            "target_id": persona.id,
            "reason_type": "HARMFUL_CONTENT",
        },
    )
    report_id = create_response.json()["id"]

    # Admin takes action
    client.patch(
        f"/api/v1/admin/reports/{report_id}/action-taken",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    # Admin checks audit logs
    response = client.get(
        "/api/v1/admin/audit-logs?action=REPORT_ACTION_TAKEN",
        headers={"Authorization": f"Bearer {admin['access_token']}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1



