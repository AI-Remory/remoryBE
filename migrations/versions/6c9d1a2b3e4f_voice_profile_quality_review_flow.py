"""voice profile quality review flow

Revision ID: 6c9d1a2b3e4f
Revises: 1a2b3c4d5e6f
Create Date: 2026-05-12 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "6c9d1a2b3e4f"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


voice_profile_review_status = sa.Enum(
    "NOT_REVIEWED",
    "USER_CONFIRMED",
    "ADMIN_APPROVED",
    "REJECTED",
    name="voiceprofilereviewstatus",
)


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def _drop_column_if_exists(table_name: str, column_name: str) -> None:
    if _has_column(table_name, column_name):
        op.drop_column(table_name, column_name)


def upgrade() -> None:
    voice_profile_review_status.create(op.get_bind(), checkfirst=True)

    # Expand status enum values in MySQL; harmlessly skipped on unsupported dialects.
    try:
        op.execute(
            sa.text(
                "ALTER TABLE persona_voice_profiles MODIFY COLUMN status "
                "ENUM('PENDING','PROCESSING','READY','FAILED','NEEDS_MORE_SAMPLES','REVOKED') NOT NULL"
            )
        )
    except Exception:
        pass

    _add_column_if_missing(
        "persona_voice_profiles",
        sa.Column("review_status", voice_profile_review_status, nullable=True),
    )
    _add_column_if_missing("persona_voice_profiles", sa.Column("reference_audio_paths_json", sa.JSON(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("total_reference_duration_ms", sa.Integer(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("quality_score", sa.Float(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("similarity_score", sa.Float(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("noise_score", sa.Float(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("review_note", sa.Text(), nullable=True))

    op.execute(sa.text("UPDATE persona_voice_profiles SET review_status = 'NOT_REVIEWED' WHERE review_status IS NULL"))

    op.alter_column(
        "persona_voice_profiles",
        "review_status",
        existing_type=voice_profile_review_status,
        nullable=False,
    )

    if not _has_index("persona_voice_profiles", "ix_persona_voice_profiles_review_status"):
        op.create_index("ix_persona_voice_profiles_review_status", "persona_voice_profiles", ["review_status"], unique=False)
    if not _has_index("persona_voice_profiles", "ix_persona_voice_profiles_reviewed_by"):
        op.create_index("ix_persona_voice_profiles_reviewed_by", "persona_voice_profiles", ["reviewed_by"], unique=False)

    try:
        op.create_foreign_key(
            "fk_persona_voice_profiles_reviewed_by_users",
            "persona_voice_profiles",
            "users",
            ["reviewed_by"],
            ["id"],
        )
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint(
            "fk_persona_voice_profiles_reviewed_by_users",
            "persona_voice_profiles",
            type_="foreignkey",
        )
    except Exception:
        pass

    if _has_index("persona_voice_profiles", "ix_persona_voice_profiles_reviewed_by"):
        op.drop_index("ix_persona_voice_profiles_reviewed_by", table_name="persona_voice_profiles")
    if _has_index("persona_voice_profiles", "ix_persona_voice_profiles_review_status"):
        op.drop_index("ix_persona_voice_profiles_review_status", table_name="persona_voice_profiles")

    _drop_column_if_exists("persona_voice_profiles", "review_note")
    _drop_column_if_exists("persona_voice_profiles", "reviewed_at")
    _drop_column_if_exists("persona_voice_profiles", "reviewed_by")
    _drop_column_if_exists("persona_voice_profiles", "noise_score")
    _drop_column_if_exists("persona_voice_profiles", "similarity_score")
    _drop_column_if_exists("persona_voice_profiles", "quality_score")
    _drop_column_if_exists("persona_voice_profiles", "total_reference_duration_ms")
    _drop_column_if_exists("persona_voice_profiles", "reference_audio_paths_json")
    _drop_column_if_exists("persona_voice_profiles", "review_status")

    try:
        op.execute(
            sa.text(
                "ALTER TABLE persona_voice_profiles MODIFY COLUMN status "
                "ENUM('PENDING','READY','FAILED','DISABLED') NOT NULL"
            )
        )
    except Exception:
        pass

    voice_profile_review_status.drop(op.get_bind(), checkfirst=True)

