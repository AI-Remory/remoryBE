"""create missing usage limit tables

Revision ID: c8f1d4a7b9e2
Revises: a4c8e2f1b9d0
Create Date: 2026-05-14 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "c8f1d4a7b9e2"
down_revision = "a4c8e2f1b9d0"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return inspect(op.get_bind()).has_table(table_name)


def _index_exists(table_name: str, index_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    inspector = inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if not _index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _index_exists(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _table_exists("usage_limits"):
        op.create_table(
            "usage_limits",
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("period_ym", sa.String(length=7), nullable=False),
            sa.Column("voice_generation_count", sa.Integer(), nullable=True),
            sa.Column("voice_generation_limit", sa.Integer(), nullable=False),
            sa.Column("stt_request_count", sa.Integer(), nullable=True),
            sa.Column("stt_request_limit", sa.Integer(), nullable=False),
            sa.Column("voice_call_seconds", sa.Integer(), nullable=True),
            sa.Column("voice_call_seconds_limit", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_usage_limits_id", "usage_limits", ["id"])
    _create_index_if_missing("ix_usage_limits_user_id", "usage_limits", ["user_id"])
    _create_index_if_missing("ix_usage_limits_period_ym", "usage_limits", ["period_ym"])
    _create_index_if_missing("ix_usage_limits_user_ym", "usage_limits", ["user_id", "period_ym"], unique=True)

    if not _table_exists("persona_usage_limits"):
        op.create_table(
            "persona_usage_limits",
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("persona_id", sa.Integer(), nullable=False),
            sa.Column("period_ym", sa.String(length=7), nullable=False),
            sa.Column("voice_generation_count", sa.Integer(), nullable=True),
            sa.Column("voice_generation_limit", sa.Integer(), nullable=False),
            sa.Column("voice_call_seconds", sa.Integer(), nullable=True),
            sa.Column("voice_call_seconds_limit", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["persona_id"], ["personas.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_persona_usage_limits_id", "persona_usage_limits", ["id"])
    _create_index_if_missing("ix_persona_usage_limits_persona_id", "persona_usage_limits", ["persona_id"])
    _create_index_if_missing("ix_persona_usage_limits_period_ym", "persona_usage_limits", ["period_ym"])
    _create_index_if_missing(
        "ix_persona_usage_limits_persona_ym",
        "persona_usage_limits",
        ["persona_id", "period_ym"],
        unique=True,
    )

    if not _table_exists("rate_limit_events"):
        op.create_table(
            "rate_limit_events",
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("endpoint", sa.String(length=255), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("count", sa.Integer(), nullable=True),
            sa.Column("window_seconds", sa.Integer(), nullable=True),
            sa.Column("blocked", sa.Boolean(), nullable=True),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing("ix_rate_limit_events_id", "rate_limit_events", ["id"])
    _create_index_if_missing("ix_rate_limit_events_user_id", "rate_limit_events", ["user_id"])
    _create_index_if_missing("ix_rate_limit_events_ip_address", "rate_limit_events", ["ip_address"])
    _create_index_if_missing("ix_rate_limit_events_endpoint", "rate_limit_events", ["endpoint"])
    _create_index_if_missing("ix_rate_limit_events_event_type", "rate_limit_events", ["event_type"])


def downgrade() -> None:
    for index_name in (
        "ix_rate_limit_events_event_type",
        "ix_rate_limit_events_endpoint",
        "ix_rate_limit_events_ip_address",
        "ix_rate_limit_events_user_id",
        "ix_rate_limit_events_id",
    ):
        _drop_index_if_exists(index_name, "rate_limit_events")
    if _table_exists("rate_limit_events"):
        op.drop_table("rate_limit_events")

    for index_name in (
        "ix_persona_usage_limits_persona_ym",
        "ix_persona_usage_limits_period_ym",
        "ix_persona_usage_limits_persona_id",
        "ix_persona_usage_limits_id",
    ):
        _drop_index_if_exists(index_name, "persona_usage_limits")
    if _table_exists("persona_usage_limits"):
        op.drop_table("persona_usage_limits")

    for index_name in (
        "ix_usage_limits_user_ym",
        "ix_usage_limits_period_ym",
        "ix_usage_limits_user_id",
        "ix_usage_limits_id",
    ):
        _drop_index_if_exists(index_name, "usage_limits")
    if _table_exists("usage_limits"):
        op.drop_table("usage_limits")
