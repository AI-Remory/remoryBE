"""voice clone profile metadata

Revision ID: d4f8a2c9b7e1
Revises: ab12cd34ef56
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "d4f8a2c9b7e1"
down_revision = "ab12cd34ef56"
branch_labels = None
depends_on = None


voice_profile_status = sa.Enum("PENDING", "READY", "FAILED", "DISABLED", name="voiceprofilestatus")


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_foreign_key(table_name: str, constraint_name: str) -> bool:
    inspector = inspect(op.get_bind())
    return any(fk["name"] == constraint_name for fk in inspector.get_foreign_keys(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    voice_profile_status.create(op.get_bind(), checkfirst=True)
    _add_column_if_missing("persona_voice_profiles", sa.Column("target_id", sa.Integer(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("provider", sa.String(length=100), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("model_name", sa.String(length=255), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("status", voice_profile_status, nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("reference_audio_count", sa.Integer(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("reference_audio_total_seconds", sa.Float(), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("voice_profile_path", sa.String(length=512), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("sample_audio_path", sa.String(length=512), nullable=True))
    _add_column_if_missing("persona_voice_profiles", sa.Column("error_message", sa.Text(), nullable=True))

    op.execute(sa.text("UPDATE persona_voice_profiles SET provider = COALESCE(voice_provider, 'mock')"))
    op.execute(sa.text("UPDATE persona_voice_profiles SET status = 'READY'"))
    op.execute(sa.text("UPDATE persona_voice_profiles SET reference_audio_count = CASE WHEN reference_voice_file_path IS NULL THEN 0 ELSE 1 END"))

    op.alter_column(
        "persona_voice_profiles",
        "provider",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "persona_voice_profiles",
        "status",
        existing_type=voice_profile_status,
        nullable=False,
    )
    op.alter_column(
        "persona_voice_profiles",
        "reference_audio_count",
        existing_type=sa.Integer(),
        nullable=False,
    )
    if not _has_index("persona_voice_profiles", "ix_persona_voice_profiles_target_id"):
        op.create_index("ix_persona_voice_profiles_target_id", "persona_voice_profiles", ["target_id"], unique=False)
    if not _has_index("persona_voice_profiles", "ix_persona_voice_profiles_status"):
        op.create_index("ix_persona_voice_profiles_status", "persona_voice_profiles", ["status"], unique=False)
    if not _has_foreign_key("persona_voice_profiles", "fk_persona_voice_profiles_target_id_targets"):
        op.create_foreign_key(
            "fk_persona_voice_profiles_target_id_targets",
            "persona_voice_profiles",
            "targets",
            ["target_id"],
            ["id"],
        )


def downgrade() -> None:
    op.drop_constraint("fk_persona_voice_profiles_target_id_targets", "persona_voice_profiles", type_="foreignkey")
    op.drop_index("ix_persona_voice_profiles_status", table_name="persona_voice_profiles")
    op.drop_index("ix_persona_voice_profiles_target_id", table_name="persona_voice_profiles")
    op.drop_column("persona_voice_profiles", "error_message")
    op.drop_column("persona_voice_profiles", "sample_audio_path")
    op.drop_column("persona_voice_profiles", "voice_profile_path")
    op.drop_column("persona_voice_profiles", "reference_audio_total_seconds")
    op.drop_column("persona_voice_profiles", "reference_audio_count")
    op.drop_column("persona_voice_profiles", "status")
    op.drop_column("persona_voice_profiles", "model_name")
    op.drop_column("persona_voice_profiles", "provider")
    op.drop_column("persona_voice_profiles", "target_id")
    voice_profile_status.drop(op.get_bind(), checkfirst=True)
