"""create missing audit logs table

Revision ID: a4c8e2f1b9d0
Revises: 7d3e9a1c5b2f
Create Date: 2026-05-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "a4c8e2f1b9d0"
down_revision = "7d3e9a1c5b2f"
branch_labels = None
depends_on = None


audit_action_enum = sa.Enum(
    "USER_SIGNUP",
    "TARGET_CREATED",
    "TARGET_UPDATED",
    "TARGET_DELETED",
    "CONSENT_CREATED",
    "CONSENT_REVOKED",
    "VERIFICATION_SUBMITTED",
    "VERIFICATION_APPROVED",
    "VERIFICATION_REJECTED",
    "VERIFICATION_NEED_MORE_INFO",
    "VERIFICATION_REVOKED",
    "PERSONA_CREATED",
    "PERSONA_CHAT_CREATED",
    "PERSONA_MESSAGE_CREATED",
    "VOICE_PROFILE_CREATED",
    "VOICE_PROFILE_REVIEWED",
    "VOICE_SYNTHESIZED",
    "VOICE_CALL_STARTED",
    "VOICE_CALL_ENDED",
    "DELETION_REQUESTED",
    "DELETION_COMPLETED",
    "DELETION_REJECTED",
    "REPORT_CREATED",
    "REPORT_RESOLVED",
    "REPORT_REVIEWING",
    "REPORT_REJECTED",
    "REPORT_ACTION_TAKEN",
    "RATE_LIMIT_BLOCKED",
    "ABNORMAL_REQUEST_BLOCKED",
    name="auditaction",
)

audit_target_type_enum = sa.Enum(
    "TARGET",
    "CONSENT",
    "VERIFICATION_REQUEST",
    "PERSONA",
    "PERSONA_CHAT",
    "PERSONA_MESSAGE",
    "VOICE_PROFILE",
    "DELETION_REQUEST",
    "REPORT",
    "USER",
    "SYSTEM",
    name="audittargettype",
)


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str]) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=False)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _table_exists(table_name) and _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _table_exists("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("action", audit_action_enum, nullable=False),
            sa.Column("target_type", audit_target_type_enum, nullable=True),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=512), nullable=True),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_audit_logs_id", "audit_logs", ["id"])
    _create_index_if_missing("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    _create_index_if_missing("ix_audit_logs_action", "audit_logs", ["action"])
    _create_index_if_missing("ix_audit_logs_target_type", "audit_logs", ["target_type"])
    _create_index_if_missing("ix_audit_logs_target_id", "audit_logs", ["target_id"])


def downgrade() -> None:
    for index_name in (
        "ix_audit_logs_target_id",
        "ix_audit_logs_target_type",
        "ix_audit_logs_action",
        "ix_audit_logs_actor_user_id",
        "ix_audit_logs_id",
    ):
        _drop_index_if_exists(index_name, "audit_logs")

    if _table_exists("audit_logs"):
        op.drop_table("audit_logs")

    audit_target_type_enum.drop(op.get_bind(), checkfirst=True)
    audit_action_enum.drop(op.get_bind(), checkfirst=True)
