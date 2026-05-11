"""Strengthen deletion request model with processing workflow

Revision ID: cd34ef56ab12
Revises: ab12cd34ef56
Create Date: 2026-05-12 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd34ef56ab12'
down_revision = 'ab12cd34ef56'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new columns: requested_at, processed_by, admin_note
    op.add_column('deletion_requests', sa.Column('requested_at', sa.DateTime(), nullable=True))
    op.add_column('deletion_requests', sa.Column('processed_by', sa.Integer(), nullable=True))
    op.add_column('deletion_requests', sa.Column('admin_note', sa.Text(), nullable=True))

    # 2. Make target_id nullable
    op.alter_column('deletion_requests', 'target_id',
                    existing_type=sa.Integer(),
                    nullable=True,
                    existing_nullable=False)

    # 3. Update requested_at for existing records - set to created_at
    op.execute(sa.text("UPDATE deletion_requests SET requested_at = created_at WHERE requested_at IS NULL"))

    # 4. Make requested_at NOT NULL after backfill
    op.alter_column('deletion_requests', 'requested_at',
                    existing_type=sa.DateTime(),
                    nullable=False)

    # 5. Add foreign key constraint for processed_by
    op.create_foreign_key(
        'fk_deletion_requests_processed_by_users',
        'deletion_requests',
        'users',
        ['processed_by'],
        ['id']
    )

    # 6. Extend status enum to include new values
    # First, update existing values by mapping old enum to new
    op.execute(sa.text("""
        ALTER TABLE deletion_requests
        MODIFY COLUMN status ENUM(
            'PENDING',
            'PROCESSING',
            'COMPLETED',
            'FAILED',
            'REJECTED',
            'CANCELLED'
        ) NOT NULL DEFAULT 'PENDING'
    """))

    # 7. Extend target_type enum to include new values
    op.execute(sa.text("""
        ALTER TABLE deletion_requests
        MODIFY COLUMN target_type ENUM(
            'TARGET',
            'TARGET_MEDIA',
            'PERSONA',
            'PERSONA_CHAT',
            'PERSONA_MESSAGE',
            'PHOTO_MEMORY',
            'STORYBOOK',
            'SHARE_LINK',
            'MEMORY_GROUP',
            'VERIFICATION_REQUEST',
            'ACCOUNT',
            'VOICE_PROFILE',
            'VOICE_CALL_SESSION'
        ) NOT NULL
    """))


def downgrade() -> None:
    # 1. Revert enum tables
    op.execute(sa.text("""
        ALTER TABLE deletion_requests
        MODIFY COLUMN target_type ENUM(
            'TARGET',
            'TARGET_MEDIA',
            'PERSONA',
            'PERSONA_CHAT',
            'PERSONA_MESSAGE',
            'PHOTO_MEMORY',
            'STORYBOOK',
            'SHARE_LINK',
            'MEMORY_GROUP',
            'VERIFICATION_REQUEST',
            'ACCOUNT'
        ) NOT NULL
    """))

    op.execute(sa.text("""
        ALTER TABLE deletion_requests
        MODIFY COLUMN status ENUM(
            'REQUESTED',
            'COMPLETED',
            'FAILED'
        ) NOT NULL DEFAULT 'REQUESTED'
    """))

    # 2. Drop foreign key
    op.drop_constraint('fk_deletion_requests_processed_by_users', 'deletion_requests', type_='foreignkey')

    # 3. Make target_id NOT NULL
    op.alter_column('deletion_requests', 'target_id',
                    existing_type=sa.Integer(),
                    nullable=False)

    # 4. Drop new columns
    op.drop_column('deletion_requests', 'admin_note')
    op.drop_column('deletion_requests', 'processed_by')
    op.drop_column('deletion_requests', 'requested_at')

