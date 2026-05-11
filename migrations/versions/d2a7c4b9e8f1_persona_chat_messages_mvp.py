"""persona chat messages mvp

Revision ID: d2a7c4b9e8f1
Revises: b8f6d1c9a2e4
Create Date: 2026-05-09 03:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2a7c4b9e8f1'
down_revision = 'b8f6d1c9a2e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('persona_chats', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('persona_messages', sa.Column('is_ai_generated', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('persona_messages', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    op.drop_column('persona_chats', 'description')
    op.drop_column('persona_chats', 'is_deleted')
    op.drop_column('persona_messages', 'audio_mime_type')
    op.drop_column('persona_messages', 'is_deleted')
    op.drop_column('persona_messages', 'updated_at')


def downgrade() -> None:
    op.add_column('persona_messages', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('persona_messages', sa.Column('audio_mime_type', sa.String(length=100), nullable=True))
    op.add_column('persona_messages', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('persona_chats', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('persona_chats', sa.Column('description', sa.Text(), nullable=True))

    op.drop_column('persona_messages', 'deleted_at')
    op.drop_column('persona_messages', 'is_ai_generated')
    op.drop_column('persona_chats', 'deleted_at')
