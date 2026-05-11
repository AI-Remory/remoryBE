"""add report model and fields

Revision ID: 1a2b3c4d5e6f
Revises: (f9b2c6d8e1a3, e46ce20a7937)
Create Date: 2026-05-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "1a2b3c4d5e6f"
down_revision = ("f9b2c6d8e1a3", "e46ce20a7937")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reporter_user_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reason_type", sa.String(50), nullable=False),
        sa.Column("reason_detail", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["users.id"], ),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_reports_id", "reports", ["id"])
    op.create_index("ix_reports_reporter_user_id", "reports", ["reporter_user_id"])
    op.create_index("ix_reports_target_type", "reports", ["target_type"])
    op.create_index("ix_reports_target_id", "reports", ["target_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_reviewed_by", "reports", ["reviewed_by"])

    # Add columns to personas table
    op.add_column("personas", sa.Column("disabled_at", sa.DateTime(), nullable=True))
    op.add_column("personas", sa.Column("disabled_reason", sa.String(255), nullable=True))

    # Add column to storybooks table
    op.add_column("storybooks", sa.Column("disabled_at", sa.DateTime(), nullable=True))

    # Add columns to persona_messages table
    op.add_column("persona_messages", sa.Column("hidden_at", sa.DateTime(), nullable=True))
    op.add_column("persona_messages", sa.Column("hidden_reason", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_index("ix_reports_reviewed_by", "reports")
    op.drop_index("ix_reports_status", "reports")
    op.drop_index("ix_reports_target_id", "reports")
    op.drop_index("ix_reports_target_type", "reports")
    op.drop_index("ix_reports_reporter_user_id", "reports")
    op.drop_index("ix_reports_id", "reports")
    op.drop_table("reports")

    op.drop_column("personas", "disabled_reason")
    op.drop_column("personas", "disabled_at")

    op.drop_column("storybooks", "disabled_at")

    op.drop_column("persona_messages", "hidden_reason")
    op.drop_column("persona_messages", "hidden_at")


