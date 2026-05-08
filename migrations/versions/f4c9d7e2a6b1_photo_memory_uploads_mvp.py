"""photo memory uploads mvp

Revision ID: f4c9d7e2a6b1
Revises: e3b8f2a6c1d5
Create Date: 2026-05-09 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4c9d7e2a6b1'
down_revision = 'e3b8f2a6c1d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('photo_memories', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('photo_memories', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('photo_memories', sa.Column('file_path', sa.String(length=512), nullable=True))
    op.add_column('photo_memories', sa.Column('original_filename', sa.String(length=512), nullable=True))
    op.add_column('photo_memories', sa.Column('stored_filename', sa.String(length=512), nullable=True))
    op.add_column('photo_memories', sa.Column('mime_type', sa.String(length=100), nullable=True))
    op.add_column('photo_memories', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('photo_memories', sa.Column('taken_at', sa.DateTime(), nullable=True))
    op.add_column('photo_memories', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('photo_memories', sa.Column('ai_caption', sa.Text(), nullable=True))
    op.add_column('photo_memories', sa.Column('emotion_keywords', sa.JSON(), nullable=True))
    op.add_column('photo_memories', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    op.execute(sa.text("UPDATE photo_memories SET title = COALESCE(photo_description, photo_original_filename, 'Untitled photo')"))
    op.execute(sa.text("UPDATE photo_memories SET description = photo_description"))
    op.execute(sa.text("UPDATE photo_memories SET file_path = photo_file_path"))
    op.execute(sa.text("UPDATE photo_memories SET original_filename = photo_original_filename"))
    op.execute(sa.text("UPDATE photo_memories SET stored_filename = SUBSTRING_INDEX(photo_file_path, '/', -1)"))
    op.execute(sa.text("UPDATE photo_memories SET mime_type = photo_mime_type"))
    op.execute(sa.text("UPDATE photo_memories SET file_size = 0 WHERE file_size IS NULL"))

    op.alter_column('photo_memories', 'title', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('photo_memories', 'file_path', existing_type=sa.String(length=512), nullable=False)
    op.alter_column('photo_memories', 'original_filename', existing_type=sa.String(length=512), nullable=False)
    op.alter_column('photo_memories', 'stored_filename', existing_type=sa.String(length=512), nullable=False)
    op.alter_column('photo_memories', 'mime_type', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('photo_memories', 'file_size', existing_type=sa.Integer(), nullable=False)

    op.drop_column('photo_memories', 'photo_description')
    op.drop_column('photo_memories', 'photo_original_filename')
    op.drop_column('photo_memories', 'photo_mime_type')
    op.drop_column('photo_memories', 'photo_file_path')
    op.drop_column('photo_memories', 'is_deleted')


def downgrade() -> None:
    op.add_column('photo_memories', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('photo_memories', sa.Column('photo_file_path', sa.String(length=512), nullable=True))
    op.add_column('photo_memories', sa.Column('photo_mime_type', sa.String(length=100), nullable=True))
    op.add_column('photo_memories', sa.Column('photo_original_filename', sa.String(length=512), nullable=True))
    op.add_column('photo_memories', sa.Column('photo_description', sa.Text(), nullable=True))

    op.execute(sa.text("UPDATE photo_memories SET photo_file_path = file_path"))
    op.execute(sa.text("UPDATE photo_memories SET photo_mime_type = mime_type"))
    op.execute(sa.text("UPDATE photo_memories SET photo_original_filename = original_filename"))
    op.execute(sa.text("UPDATE photo_memories SET photo_description = description"))

    op.alter_column('photo_memories', 'photo_file_path', existing_type=sa.String(length=512), nullable=False)
    op.alter_column('photo_memories', 'photo_mime_type', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('photo_memories', 'photo_original_filename', existing_type=sa.String(length=512), nullable=False)

    op.drop_column('photo_memories', 'deleted_at')
    op.drop_column('photo_memories', 'emotion_keywords')
    op.drop_column('photo_memories', 'ai_caption')
    op.drop_column('photo_memories', 'location')
    op.drop_column('photo_memories', 'taken_at')
    op.drop_column('photo_memories', 'file_size')
    op.drop_column('photo_memories', 'mime_type')
    op.drop_column('photo_memories', 'stored_filename')
    op.drop_column('photo_memories', 'original_filename')
    op.drop_column('photo_memories', 'file_path')
    op.drop_column('photo_memories', 'description')
    op.drop_column('photo_memories', 'title')
