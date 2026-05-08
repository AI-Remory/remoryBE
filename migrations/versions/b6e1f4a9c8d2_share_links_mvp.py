"""share links mvp

Revision ID: b6e1f4a9c8d2
Revises: a5d9c3e7b2f4
Create Date: 2026-05-09 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'b6e1f4a9c8d2'
down_revision = 'a5d9c3e7b2f4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f('ix_share_links_share_token'), table_name='share_links')
    op.alter_column('share_links', 'share_token',
                    existing_type=mysql.VARCHAR(length=64),
                    type_=sa.String(length=128),
                    new_column_name='token',
                    existing_nullable=False)
    op.alter_column('share_links', 'shared_by_user_id',
                    existing_type=sa.Integer(),
                    new_column_name='owner_id',
                    existing_nullable=False)
    op.create_index(op.f('ix_share_links_token'), 'share_links', ['token'], unique=True)
    op.create_index(op.f('ix_share_links_owner_id'), 'share_links', ['owner_id'], unique=False)

    op.add_column('share_links', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('share_links', sa.Column('expires_at', sa.DateTime(), nullable=True))
    op.add_column('share_links', sa.Column('disabled_at', sa.DateTime(), nullable=True))

    op.drop_column('share_links', 'permission')
    op.drop_column('share_links', 'description')
    op.drop_column('share_links', 'is_expired')
    op.drop_column('share_links', 'is_deleted')


def downgrade() -> None:
    op.add_column('share_links', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('share_links', sa.Column('is_expired', sa.Boolean(), nullable=True))
    op.add_column('share_links', sa.Column('description', sa.Text(), nullable=True))
    op.add_column(
        'share_links',
        sa.Column('permission', sa.Enum('VIEW', 'COMMENT', 'EDIT', name='sharepermission'), nullable=False),
    )
    op.execute(sa.text("UPDATE share_links SET permission = 'VIEW'"))
    op.execute(sa.text("UPDATE share_links SET is_expired = CASE WHEN is_active = 1 THEN 0 ELSE 1 END"))

    op.drop_column('share_links', 'disabled_at')
    op.drop_column('share_links', 'expires_at')
    op.drop_column('share_links', 'is_active')
    op.drop_index(op.f('ix_share_links_owner_id'), table_name='share_links')
    op.drop_index(op.f('ix_share_links_token'), table_name='share_links')
    op.alter_column('share_links', 'owner_id',
                    existing_type=sa.Integer(),
                    new_column_name='shared_by_user_id',
                    existing_nullable=False)
    op.alter_column('share_links', 'token',
                    existing_type=sa.String(length=128),
                    type_=mysql.VARCHAR(length=64),
                    new_column_name='share_token',
                    existing_nullable=False)
    op.create_index(op.f('ix_share_links_share_token'), 'share_links', ['share_token'], unique=True)
