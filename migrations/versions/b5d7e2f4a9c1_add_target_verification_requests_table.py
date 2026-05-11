"""add target verification requests table

Revision ID: b5d7e2f4a9c1
Revises: a9c3d1e8f2b4
Create Date: 2026-05-11 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5d7e2f4a9c1'
down_revision = 'a9c3d1e8f2b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'target_verification_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('verification_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('document_file_path', sa.String(length=512), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['targets.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_filename'),
    )

    op.create_index(
        'ix_target_verification_requests_user_id',
        'target_verification_requests',
        ['user_id'],
    )
    op.create_index(
        'ix_target_verification_requests_target_id',
        'target_verification_requests',
        ['target_id'],
    )
    op.create_index(
        'ix_target_verification_requests_status',
        'target_verification_requests',
        ['status'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_target_verification_requests_status',
        table_name='target_verification_requests',
    )
    op.drop_index(
        'ix_target_verification_requests_target_id',
        table_name='target_verification_requests',
    )
    op.drop_index(
        'ix_target_verification_requests_user_id',
        table_name='target_verification_requests',
    )
    op.drop_table('target_verification_requests')

