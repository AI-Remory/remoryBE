"""voice clone profile metadata

Revision ID: d4f8a2c9b7e1
Revises: ab12cd34ef56
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4f8a2c9b7e1"
down_revision = "ab12cd34ef56"
branch_labels = None
depends_on = None


voice_profile_status = sa.Enum("PENDING", "READY", "FAILED", "DISABLED", name="voiceprofilestatus")


def upgrade() -> None:
    voice_profile_status.create(op.get_bind(), checkfirst=True)
    op.add_column("persona_voice_profiles", sa.Column("target_id", sa.Integer(), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("provider", sa.String(length=100), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("model_name", sa.String(length=255), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("status", voice_profile_status, nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("reference_audio_count", sa.Integer(), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("reference_audio_total_seconds", sa.Float(), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("voice_profile_path", sa.String(length=512), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("sample_audio_path", sa.String(length=512), nullable=True))
    op.add_column("persona_voice_profiles", sa.Column("error_message", sa.Text(), nullable=True))

    op.execute(sa.text("UPDATE persona_voice_profiles SET provider = COALESCE(voice_provider, 'mock')"))
    op.execute(sa.text("UPDATE persona_voice_profiles SET status = 'READY'"))
    op.execute(sa.text("UPDATE persona_voice_profiles SET reference_audio_count = CASE WHEN reference_voice_file_path IS NULL THEN 0 ELSE 1 END"))

    op.alter_column("persona_voice_profiles", "provider", nullable=False)
    op.alter_column("persona_voice_profiles", "status", nullable=False)
    op.alter_column("persona_voice_profiles", "reference_audio_count", nullable=False)
    op.create_index("ix_persona_voice_profiles_target_id", "persona_voice_profiles", ["target_id"], unique=False)
    op.create_index("ix_persona_voice_profiles_status", "persona_voice_profiles", ["status"], unique=False)
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
