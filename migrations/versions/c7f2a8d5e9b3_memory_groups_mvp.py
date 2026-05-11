"""memory groups mvp

Revision ID: c7f2a8d5e9b3
Revises: b6e1f4a9c8d2
Create Date: 2026-05-09 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'c7f2a8d5e9b3'
down_revision = 'b6e1f4a9c8d2'
branch_labels = None
depends_on = None


def _drop_foreign_keys_for_columns(table_name: str, column_names: set[str]) -> None:
    """Drop foreign keys that are bound to the given columns.

    MySQL auto-generates FK names for unnamed constraints, so the live name may
    differ across local and CI databases.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for foreign_key in inspector.get_foreign_keys(table_name):
        constrained_columns = set(foreign_key.get("constrained_columns") or [])
        constraint_name = foreign_key.get("name")
        if constraint_name and constrained_columns == column_names:
            op.drop_constraint(constraint_name, table_name, type_="foreignkey")


def upgrade() -> None:
    _drop_foreign_keys_for_columns('memory_groups', {'creator_id'})
    op.drop_index(op.f('ix_memory_groups_creator_id'), table_name='memory_groups')
    op.alter_column('memory_groups', 'creator_id',
                    existing_type=sa.Integer(),
                    new_column_name='owner_id',
                    existing_nullable=False)
    op.create_index(op.f('ix_memory_groups_owner_id'), 'memory_groups', ['owner_id'], unique=False)
    op.create_foreign_key('fk_memory_groups_owner_id_users', 'memory_groups', 'users', ['owner_id'], ['id'])
    op.add_column('memory_groups', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.drop_index(op.f('ix_memory_groups_group_code'), table_name='memory_groups')
    op.drop_column('memory_groups', 'group_code')
    op.drop_column('memory_groups', 'invite_link_token')
    op.drop_column('memory_groups', 'profile_image_path')
    op.drop_column('memory_groups', 'is_deleted')

    op.add_column('group_members', sa.Column('role', sa.String(length=32), nullable=False, server_default='MEMBER'))
    op.add_column('group_members', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.execute(sa.text("UPDATE group_members SET role = 'MEMBER'"))
    op.execute(
        sa.text(
            """
            UPDATE group_members gm
            JOIN memory_groups mg ON mg.id = gm.group_id
            SET gm.role = 'OWNER'
            WHERE gm.user_id = mg.owner_id
            """
        )
    )
    op.drop_column('group_members', 'permission')
    op.drop_column('group_members', 'is_deleted')
    op.alter_column(
        'group_members',
        'role',
        existing_type=sa.String(length=32),
        type_=sa.Enum('OWNER', 'MEMBER', 'VIEWER', name='groupmemberrole'),
        existing_nullable=False,
        server_default=None,
    )

    op.alter_column('group_storybooks', 'shared_by_user_id',
                    existing_type=sa.Integer(),
                    new_column_name='shared_by',
                    existing_nullable=False)
    op.create_index(op.f('ix_group_storybooks_shared_by'), 'group_storybooks', ['shared_by'], unique=False)
    op.add_column('group_storybooks', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.drop_column('group_storybooks', 'is_deleted')


def downgrade() -> None:
    op.add_column('group_storybooks', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.drop_column('group_storybooks', 'deleted_at')
    op.drop_index(op.f('ix_group_storybooks_shared_by'), table_name='group_storybooks')
    op.alter_column('group_storybooks', 'shared_by',
                    existing_type=sa.Integer(),
                    new_column_name='shared_by_user_id',
                    existing_nullable=False)

    op.alter_column('group_members', 'role',
                    existing_type=sa.Enum('OWNER', 'MEMBER', 'VIEWER', name='groupmemberrole'),
                    type_=sa.String(length=32),
                    existing_nullable=False)
    op.add_column('group_members', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        'group_members',
        sa.Column('permission', mysql.ENUM('VIEW', 'COMMENT', 'EDIT'), nullable=False, server_default='VIEW'),
    )
    op.drop_column('group_members', 'deleted_at')
    op.drop_column('group_members', 'role')

    op.add_column('memory_groups', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('memory_groups', sa.Column('profile_image_path', sa.String(length=512), nullable=True))
    op.add_column('memory_groups', sa.Column('invite_link_token', sa.String(length=64), nullable=True))
    op.add_column('memory_groups', sa.Column('group_code', sa.String(length=20), nullable=True))
    op.execute(sa.text("UPDATE memory_groups SET group_code = CONCAT('group-', id) WHERE group_code IS NULL"))
    op.alter_column('memory_groups', 'group_code', existing_type=sa.String(length=20), nullable=False)
    op.create_index(op.f('ix_memory_groups_group_code'), 'memory_groups', ['group_code'], unique=True)
    op.drop_column('memory_groups', 'deleted_at')
    _drop_foreign_keys_for_columns('memory_groups', {'owner_id'})
    op.drop_index(op.f('ix_memory_groups_owner_id'), table_name='memory_groups')
    op.alter_column('memory_groups', 'owner_id',
                    existing_type=sa.Integer(),
                    new_column_name='creator_id',
                    existing_nullable=False)
    op.create_index(op.f('ix_memory_groups_creator_id'), 'memory_groups', ['creator_id'], unique=False)
    op.create_foreign_key('fk_memory_groups_creator_id_users', 'memory_groups', 'users', ['creator_id'], ['id'])
