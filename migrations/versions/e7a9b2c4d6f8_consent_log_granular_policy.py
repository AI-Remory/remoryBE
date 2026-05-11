"""consent log granular policy

Revision ID: e7a9b2c4d6f8
Revises: d4f8a2c9b7e1
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "e7a9b2c4d6f8"
down_revision = "d4f8a2c9b7e1"
branch_labels = None
depends_on = None


CONSENT_ENUM_VALUES = (
    "TARGET_PROFILE_CONSENT",
    "PHOTO_UPLOAD_CONSENT",
    "VOICE_UPLOAD_CONSENT",
    "VOICE_CLONING_CONSENT",
    "AI_PERSONA_CREATION_CONSENT",
    "AI_RESPONSE_NOTICE_CONSENT",
    "STORYBOOK_SHARE_CONSENT",
    "GROUP_SHARE_CONSENT",
    "DATA_RETENTION_CONSENT",
    "THIRD_PARTY_AI_PROCESSING_CONSENT",
    "VOICE_COLLECTION",
    "PHOTO_COLLECTION",
    "PERSONA_CREATION",
    "DATA_USAGE",
    "AI_PROCESSING",
    "AI_RESPONSE_NOTICE",
    "STORYBOOK_SHARE",
)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def _alter_consent_type_enum() -> None:
    values = ",\n                ".join(f"'{value}'" for value in CONSENT_ENUM_VALUES)
    op.execute(
        sa.text(
            f"""
            ALTER TABLE consent_logs
            MODIFY COLUMN consent_type ENUM(
                {values}
            ) NOT NULL
            """
        )
    )


def upgrade() -> None:
    _alter_consent_type_enum()
    _add_column_if_missing("consent_logs", sa.Column("consent_version", sa.String(length=50), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("consent_text_snapshot", sa.Text(), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("is_agreed", sa.Boolean(), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("agreed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("ip_address", sa.String(length=45), nullable=True))
    _add_column_if_missing("consent_logs", sa.Column("user_agent", sa.String(length=512), nullable=True))

    op.execute(sa.text("UPDATE consent_logs SET consent_version = COALESCE(consent_version, 'v1')"))
    op.execute(sa.text("UPDATE consent_logs SET is_agreed = COALESCE(is_agreed, is_consented)"))
    op.execute(
        sa.text(
            """
            UPDATE consent_logs
            SET agreed_at = CASE
                WHEN is_agreed = 1 AND agreed_at IS NULL THEN created_at
                ELSE agreed_at
            END
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE consent_logs
            SET revoked_at = CASE
                WHEN is_agreed = 0 AND revoked_at IS NULL THEN updated_at
                ELSE revoked_at
            END
            """
        )
    )
    op.alter_column(
        "consent_logs",
        "consent_version",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.alter_column(
        "consent_logs",
        "is_agreed",
        existing_type=sa.Boolean(),
        nullable=False,
    )


def downgrade() -> None:
    for column_name in (
        "user_agent",
        "ip_address",
        "revoked_at",
        "agreed_at",
        "is_agreed",
        "consent_text_snapshot",
        "consent_version",
    ):
        if _has_column("consent_logs", column_name):
            op.drop_column("consent_logs", column_name)

    op.execute(
        sa.text(
            """
            ALTER TABLE consent_logs
            MODIFY COLUMN consent_type ENUM(
                'VOICE_COLLECTION',
                'PHOTO_COLLECTION',
                'PERSONA_CREATION',
                'DATA_USAGE',
                'AI_PROCESSING',
                'AI_RESPONSE_NOTICE',
                'STORYBOOK_SHARE'
            ) NOT NULL
            """
        )
    )
