"""voice call sessions

Revision ID: 7d3e9a1c5b2f
Revises: 6c9d1a2b3e4f
Create Date: 2026-05-12 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7d3e9a1c5b2f"
down_revision = "6c9d1a2b3e4f"
branch_labels = None
depends_on = None


voice_call_session_status = sa.Enum(
    "CONNECTED",
    "ACTIVE",
    "ENDED",
    "FAILED",
    name="voicecallsessionstatus",
)


def upgrade() -> None:
    op.create_table(
        "voice_call_sessions",
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.Column("status", voice_call_session_status, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["persona_chats.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_voice_call_sessions_chat_id"), "voice_call_sessions", ["chat_id"], unique=False)
    op.create_index(op.f("ix_voice_call_sessions_id"), "voice_call_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_voice_call_sessions_persona_id"), "voice_call_sessions", ["persona_id"], unique=False)
    op.create_index(op.f("ix_voice_call_sessions_status"), "voice_call_sessions", ["status"], unique=False)
    op.create_index(op.f("ix_voice_call_sessions_user_id"), "voice_call_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_voice_call_sessions_user_id"), table_name="voice_call_sessions")
    op.drop_index(op.f("ix_voice_call_sessions_status"), table_name="voice_call_sessions")
    op.drop_index(op.f("ix_voice_call_sessions_persona_id"), table_name="voice_call_sessions")
    op.drop_index(op.f("ix_voice_call_sessions_id"), table_name="voice_call_sessions")
    op.drop_index(op.f("ix_voice_call_sessions_chat_id"), table_name="voice_call_sessions")
    op.drop_table("voice_call_sessions")
    voice_call_session_status.drop(op.get_bind(), checkfirst=True)
