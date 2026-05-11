"""harden target verification requests

Revision ID: f9b2c6d8e1a3
Revises: e7a9b2c4d6f8
Create Date: 2026-05-12 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f9b2c6d8e1a3"
down_revision = "e7a9b2c4d6f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "target_verification_requests",
        sa.Column("submitted_file_path", sa.String(length=512), nullable=True),
    )
    op.add_column("target_verification_requests", sa.Column("applicant_note", sa.Text(), nullable=True))
    op.add_column("target_verification_requests", sa.Column("admin_note", sa.Text(), nullable=True))
    op.add_column("target_verification_requests", sa.Column("expires_at", sa.DateTime(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE target_verification_requests
            SET submitted_file_path = COALESCE(document_file_path, '')
            WHERE submitted_file_path IS NULL
            """
        )
    )
    op.execute(sa.text("UPDATE target_verification_requests SET status = UPPER(status)"))
    op.execute(sa.text("UPDATE target_verification_requests SET verification_type = UPPER(verification_type)"))

    op.alter_column(
        "target_verification_requests",
        "submitted_file_path",
        existing_type=sa.String(length=512),
        nullable=False,
    )
    op.alter_column(
        "target_verification_requests",
        "mime_type",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "target_verification_requests",
        "file_size",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE target_verification_requests SET status = LOWER(status)"))
    op.execute(sa.text("UPDATE target_verification_requests SET verification_type = LOWER(verification_type)"))

    op.drop_column("target_verification_requests", "expires_at")
    op.drop_column("target_verification_requests", "admin_note")
    op.drop_column("target_verification_requests", "applicant_note")
    op.drop_column("target_verification_requests", "submitted_file_path")
