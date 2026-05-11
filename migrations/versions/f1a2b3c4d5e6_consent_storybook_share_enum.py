"""consent share enum extension

Revision ID: f1a2b3c4d5e6
Revises: d8a4b7c1e6f9
Create Date: 2026-05-11 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'd8a4b7c1e6f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE consent_logs
            MODIFY COLUMN consent_type ENUM(
                'VOICE_COLLECTION',
                'PHOTO_COLLECTION',
                'PERSONA_CREATION',
                'DATA_USAGE',
                'AI_PROCESSING',
                'AI_RESPONSE_NOTICE',
                'STORYBOOK_SHARE'
            ) NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE consent_logs
            MODIFY COLUMN consent_type ENUM(
                'VOICE_COLLECTION',
                'PHOTO_COLLECTION',
                'PERSONA_CREATION',
                'DATA_USAGE',
                'AI_PROCESSING'
            ) NOT NULL
            """
        )
    )


