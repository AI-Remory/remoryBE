from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa
from sqlalchemy import inspect, text

from app.models.audit_log import AuditLog
from tests.conftest import TestingSessionLocal, engine


def test_audit_logs_repair_migration_creates_table_and_indexes():
    from migrations.versions import a4c8e2f1b9d0_create_missing_audit_logs_table as migration

    with engine.begin() as connection:
        AuditLog.__table__.drop(bind=connection, checkfirst=True)
        context = MigrationContext.configure(connection)
        migration.op = Operations(context)

        migration.upgrade()

        inspector = inspect(connection)
        columns = {column["name"] for column in inspector.get_columns("audit_logs")}
        indexes = {index["name"] for index in inspector.get_indexes("audit_logs")}

        assert migration.down_revision == "7d3e9a1c5b2f"
        assert {
            "id",
            "actor_user_id",
            "action",
            "target_type",
            "target_id",
            "description",
            "metadata_json",
            "ip_address",
            "user_agent",
            "created_at",
            "updated_at",
        }.issubset(columns)
        assert {
            "ix_audit_logs_id",
            "ix_audit_logs_actor_user_id",
            "ix_audit_logs_action",
            "ix_audit_logs_target_type",
            "ix_audit_logs_target_id",
        }.issubset(indexes)


def test_create_consent_writes_audit_log(client, auth_headers, created_target):
    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": created_target["id"],
            "consent_type": "ai_persona_creation_consent",
            "is_agreed": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    consent_id = response.json()["id"]

    db = TestingSessionLocal()
    try:
        count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM audit_logs
                WHERE action = 'CONSENT_CREATED' AND target_id = :target_id
                """
            ),
            {"target_id": consent_id},
        ).scalar_one()
        assert count == 1
    finally:
        db.close()


def test_create_consent_recovers_when_audit_log_insert_fails(client, auth_headers, created_target):
    AuditLog.__table__.drop(bind=engine, checkfirst=True)

    response = client.post(
        "/api/v1/consents",
        json={
            "target_id": created_target["id"],
            "consent_type": "ai_response_notice_consent",
            "is_agreed": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["consent_type"] == "ai_response_notice_consent"

    listed = client.get(f"/api/v1/targets/{created_target['id']}/consents", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == payload["id"]

    db = TestingSessionLocal()
    try:
        total = db.execute(text("SELECT COUNT(*) FROM consent_logs")).scalar_one()
        assert total >= 1
    finally:
        db.close()
