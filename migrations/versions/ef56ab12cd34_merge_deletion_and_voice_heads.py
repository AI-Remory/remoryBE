"""Merge deletion and voice profile migration heads

Revision ID: ef56ab12cd34
Revises: cd34ef56ab12, f9b2c6d8e1a3
Create Date: 2026-05-12 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef56ab12cd34'
down_revision = ('cd34ef56ab12', 'f9b2c6d8e1a3')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge revision to consolidate parallel migration branches
    pass


def downgrade() -> None:
    # No-op downgrade for merge revision
    pass

