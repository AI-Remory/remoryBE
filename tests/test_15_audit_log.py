"""Tests for audit log functionality."""

from app.models.audit_log import AuditAction, AuditTargetType
from app.services.audit_log_service import AuditLogService


def test_audit_log_created_on_deletion_completion(client, auth_headers, created_target):
    """Create deletion request and verify audit log."""
    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "TARGET", "target_id": created_target["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "COMPLETED"


def test_admin_can_list_audit_logs(client, admin_token):
    """Admin can list audit logs."""
    response = client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_admin_can_filter_audit_logs_by_action(client, auth_headers, admin_token, created_target):
    """Admin can filter audit logs by action."""
    # Create a deletion request to generate an audit log
    response = client.post(
        "/api/v1/deletion-requests",
        json={"target_type": "TARGET", "target_id": created_target["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201

    # Query audit logs
    admin_response = client.get(
        "/api/v1/admin/audit-logs?action=DELETION_REQUESTED",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_response.status_code == 200


def test_general_user_cannot_access_audit_logs(client, auth_headers):
    """General user cannot access audit logs."""
    response = client.get(
        "/api/v1/admin/audit-logs",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_audit_log_sanitizes_sensitive_metadata():
    """Audit log service sanitizes sensitive fields."""
    metadata = {
        "password": "secretpass",
        "token": "token123",
        "safe_field": "safe_value",
    }

    sanitized = AuditLogService._sanitize_metadata(metadata)

    assert sanitized["password"] == "***REDACTED***"
    assert sanitized["token"] == "***REDACTED***"
    assert sanitized["safe_field"] == "safe_value"


def test_audit_log_sanitizes_nested_metadata():
    """Audit log service sanitizes nested sensitive fields."""
    metadata = {
        "user": {
            "name": "John",
            "password": "secret",
        },
        "safe": "value",
    }

    sanitized = AuditLogService._sanitize_metadata(metadata)

    assert sanitized["user"]["password"] == "***REDACTED***"
    assert sanitized["user"]["name"] == "John"
    assert sanitized["safe"] == "value"



