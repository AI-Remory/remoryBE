"""target media upload metadata

Revision ID: 69914db3a15d
Revises: 3ad8bb9a719c
Create Date: 2026-05-09 01:49:09.392382

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '69914db3a15d'
down_revision = '3ad8bb9a719c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('target_media', sa.Column('uploaded_by', sa.Integer(), nullable=True))
    op.add_column('target_media', sa.Column('stored_filename', sa.String(length=512), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE target_media tm
            JOIN targets t ON t.id = tm.target_id
            SET tm.uploaded_by = t.user_id
            WHERE tm.uploaded_by IS NULL
            """
        )
    )
    op.execute(sa.text("UPDATE target_media SET stored_filename = SUBSTRING_INDEX(file_path, '/', -1) WHERE stored_filename IS NULL"))

    op.alter_column('target_media', 'uploaded_by', existing_type=sa.Integer(), nullable=False)
    op.alter_column('target_media', 'stored_filename', existing_type=sa.String(length=512), nullable=False)

    # Convert enum AUDIO -> VOICE safely
    op.execute(sa.text("ALTER TABLE target_media MODIFY COLUMN media_type ENUM('IMAGE','AUDIO','VOICE') NOT NULL"))
    op.execute(sa.text("UPDATE target_media SET media_type = 'VOICE' WHERE media_type = 'AUDIO'"))
    op.alter_column('target_media', 'media_type',
               existing_type=mysql.ENUM('IMAGE', 'AUDIO', 'VOICE', collation='utf8mb4_unicode_ci'),
               type_=sa.Enum('IMAGE', 'VOICE', name='mediatype'),
               existing_nullable=False)
    op.create_index(op.f('ix_target_media_uploaded_by'), 'target_media', ['uploaded_by'], unique=False)
    op.create_foreign_key('fk_target_media_uploaded_by_users', 'target_media', 'users', ['uploaded_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_target_media_uploaded_by_users', 'target_media', type_='foreignkey')
    op.drop_index(op.f('ix_target_media_uploaded_by'), table_name='target_media')
    op.execute(sa.text("ALTER TABLE target_media MODIFY COLUMN media_type ENUM('IMAGE','AUDIO','VOICE') NOT NULL"))
    op.execute(sa.text("UPDATE target_media SET media_type = 'AUDIO' WHERE media_type = 'VOICE'"))
    op.alter_column('target_media', 'media_type',
               existing_type=mysql.ENUM('IMAGE', 'AUDIO', 'VOICE', collation='utf8mb4_unicode_ci'),
               type_=mysql.ENUM('IMAGE', 'AUDIO', collation='utf8mb4_unicode_ci'),
               existing_nullable=False)
    op.drop_column('target_media', 'stored_filename')
    op.drop_column('target_media', 'uploaded_by')

