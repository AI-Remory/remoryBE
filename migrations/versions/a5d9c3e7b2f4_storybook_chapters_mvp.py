"""storybook chapters mvp

Revision ID: a5d9c3e7b2f4
Revises: f4c9d7e2a6b1
Create Date: 2026-05-09 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5d9c3e7b2f4'
down_revision = 'f4c9d7e2a6b1'
branch_labels = None
depends_on = None


def _drop_foreign_keys_for_columns(table_name: str, column_names: set[str]) -> None:
    """Drop foreign keys that are bound to the given columns.

    MySQL auto-generates FK names when Alembic does not specify one. Looking up
    the live constraint name keeps this migration valid across fresh databases
    and CI environments.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for foreign_key in inspector.get_foreign_keys(table_name):
        constrained_columns = set(foreign_key.get("constrained_columns") or [])
        constraint_name = foreign_key.get("name")
        if constraint_name and constrained_columns == column_names:
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")


def upgrade() -> None:
    op.add_column('storybooks', sa.Column('photo_memory_id', sa.Integer(), nullable=True))
    op.add_column('storybooks', sa.Column('interview_session_id', sa.Integer(), nullable=True))
    op.add_column('storybooks', sa.Column('summary', sa.Text(), nullable=True))
    op.add_column('storybooks', sa.Column('source_type', sa.String(length=32), nullable=False, server_default='INTERVIEW'))
    op.add_column('storybooks', sa.Column('status', sa.String(length=32), nullable=False, server_default='DRAFT'))
    op.add_column('storybooks', sa.Column('visibility', sa.String(length=32), nullable=False, server_default='PRIVATE'))
    op.add_column('storybooks', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    op.create_index(op.f('ix_storybooks_photo_memory_id'), 'storybooks', ['photo_memory_id'], unique=False)
    op.create_index(op.f('ix_storybooks_interview_session_id'), 'storybooks', ['interview_session_id'], unique=False)
    op.create_foreign_key('fk_storybooks_photo_memory_id', 'storybooks', 'photo_memories', ['photo_memory_id'], ['id'])
    op.create_foreign_key('fk_storybooks_interview_session_id', 'storybooks', 'ai_interview_sessions', ['interview_session_id'], ['id'])

    op.execute(sa.text("UPDATE storybooks SET summary = description WHERE summary IS NULL"))
    op.execute(sa.text("UPDATE storybooks SET status = CASE WHEN is_published = 1 THEN 'GENERATED' ELSE 'DRAFT' END"))

    op.drop_column('storybooks', 'cover_image_path')
    op.drop_column('storybooks', 'description')
    op.drop_column('storybooks', 'is_published')
    op.drop_column('storybooks', 'is_deleted')
    _drop_foreign_keys_for_columns('storybooks', {'target_id'})
    op.drop_index(op.f('ix_storybooks_target_id'), table_name='storybooks')
    op.drop_column('storybooks', 'target_id')

    op.add_column('story_chapters', sa.Column('order_index', sa.Integer(), nullable=True))
    op.add_column('story_chapters', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE story_chapters SET order_index = chapter_order"))
    op.alter_column('story_chapters', 'order_index', existing_type=sa.Integer(), nullable=False)
    op.drop_column('story_chapters', 'chapter_order')
    op.drop_column('story_chapters', 'is_deleted')

    op.add_column('story_voice_narrations', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.drop_column('story_voice_narrations', 'is_deleted')

    op.alter_column(
        'storybooks',
        'source_type',
        existing_type=sa.String(length=32),
        type_=sa.Enum('INTERVIEW', 'PHOTO_MEMORY', 'SELF_STORY', name='storybooksource_type'),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        'storybooks',
        'status',
        existing_type=sa.String(length=32),
        type_=sa.Enum('DRAFT', 'GENERATED', 'FAILED', name='storybookstatus'),
        existing_nullable=False,
        server_default=None,
    )
    op.alter_column(
        'storybooks',
        'visibility',
        existing_type=sa.String(length=32),
        type_=sa.Enum('PRIVATE', 'LINK', 'GROUP', 'PUBLIC', name='storybookvisibility'),
        existing_nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    op.alter_column('storybooks', 'visibility', existing_type=sa.Enum('PRIVATE', 'LINK', 'GROUP', 'PUBLIC', name='storybookvisibility'), type_=sa.String(length=32), existing_nullable=False)
    op.alter_column('storybooks', 'status', existing_type=sa.Enum('DRAFT', 'GENERATED', 'FAILED', name='storybookstatus'), type_=sa.String(length=32), existing_nullable=False)
    op.alter_column('storybooks', 'source_type', existing_type=sa.Enum('INTERVIEW', 'PHOTO_MEMORY', 'SELF_STORY', name='storybooksource_type'), type_=sa.String(length=32), existing_nullable=False)

    op.add_column('story_voice_narrations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.drop_column('story_voice_narrations', 'deleted_at')

    op.add_column('story_chapters', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('story_chapters', sa.Column('chapter_order', sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE story_chapters SET chapter_order = order_index"))
    op.alter_column('story_chapters', 'chapter_order', existing_type=sa.Integer(), nullable=False)
    op.drop_column('story_chapters', 'deleted_at')
    op.drop_column('story_chapters', 'order_index')

    op.add_column('storybooks', sa.Column('target_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_storybooks_target_id'), 'storybooks', ['target_id'], unique=False)
    op.create_foreign_key('storybooks_ibfk_2', 'storybooks', 'targets', ['target_id'], ['id'])
    op.add_column('storybooks', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('storybooks', sa.Column('is_published', sa.Boolean(), nullable=True))
    op.add_column('storybooks', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('storybooks', sa.Column('cover_image_path', sa.String(length=512), nullable=True))
    op.execute(sa.text("UPDATE storybooks SET description = summary"))
    op.execute(sa.text("UPDATE storybooks SET is_published = CASE WHEN status = 'GENERATED' THEN 1 ELSE 0 END"))

    op.drop_constraint('fk_storybooks_interview_session_id', 'storybooks', type_='foreignkey')
    op.drop_constraint('fk_storybooks_photo_memory_id', 'storybooks', type_='foreignkey')
    op.drop_index(op.f('ix_storybooks_interview_session_id'), table_name='storybooks')
    op.drop_index(op.f('ix_storybooks_photo_memory_id'), table_name='storybooks')
    op.drop_column('storybooks', 'deleted_at')
    op.drop_column('storybooks', 'visibility')
    op.drop_column('storybooks', 'status')
    op.drop_column('storybooks', 'source_type')
    op.drop_column('storybooks', 'summary')
    op.drop_column('storybooks', 'interview_session_id')
    op.drop_column('storybooks', 'photo_memory_id')
