"""verification request deletion policy

Revision ID: c1d2e3f4a5b6
Revises: f1a2b3c4d5e6
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "b5d7e2f4a9c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE deletion_requests
            MODIFY COLUMN target_type ENUM(
                'TARGET',
                'TARGET_MEDIA',
                'VERIFICATION_REQUEST',
                'PERSONA',
                'PERSONA_CHAT',
                'PERSONA_MESSAGE',
                'PHOTO_MEMORY',
                'STORYBOOK',
                'SHARE_LINK',
                'MEMORY_GROUP',
                'ACCOUNT'
            ) NOT NULL
            """
        )
    )

    op.alter_column(
        'target_verification_requests',
        'document_file_path',
        existing_type=sa.String(length=512),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(sa.text("UPDATE deletion_requests SET target_type = 'TARGET' WHERE target_type = 'VERIFICATION_REQUEST'"))
    op.execute(
        sa.text(
            """
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
                'ACCOUNT'
            ) NOT NULL
            """
        )
    )

    op.execute(sa.text("UPDATE target_verification_requests SET document_file_path = '' WHERE document_file_path IS NULL"))
    op.alter_column(
        'target_verification_requests',
        'document_file_path',
        existing_type=sa.String(length=512),
        nullable=False,
    )


