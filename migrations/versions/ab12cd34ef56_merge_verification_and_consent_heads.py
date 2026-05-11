"""merge head: c1d2e3f4a5b6 and f1a2b3c4d5e6

Revision ID: ab12cd34ef56
Revises: c1d2e3f4a5b6, f1a2b3c4d5e6
Create Date: 2026-05-12 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab12cd34ef56'
down_revision = ('c1d2e3f4a5b6', 'f1a2b3c4d5e6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge revision to resolve multiple heads created by recent feature merges.
    pass


def downgrade() -> None:
    # No-op downgrade for merge revision.
    pass

