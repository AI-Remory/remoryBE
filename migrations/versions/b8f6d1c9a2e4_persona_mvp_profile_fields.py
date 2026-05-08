"""persona mvp profile fields

Revision ID: b8f6d1c9a2e4
Revises: 69914db3a15d
Create Date: 2026-05-09 03:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8f6d1c9a2e4'
down_revision = '69914db3a15d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('personas', sa.Column('persona_name', sa.String(length=255), nullable=True))
    op.add_column('personas', sa.Column('memory_summary', sa.Text(), nullable=True))
    op.add_column('personas', sa.Column('system_prompt', sa.Text(), nullable=True))
    op.add_column('persona_voice_profiles', sa.Column('metadata', sa.JSON(), nullable=True))

    op.execute(sa.text("ALTER TABLE personas MODIFY COLUMN status ENUM('CREATING','ACTIVE','INACTIVE','PENDING','READY','FAILED') NOT NULL"))
    op.execute(sa.text("UPDATE personas SET status = 'PENDING' WHERE status = 'CREATING'"))
    op.execute(sa.text("UPDATE personas SET status = 'READY' WHERE status = 'ACTIVE'"))
    op.execute(sa.text("UPDATE personas SET status = 'FAILED' WHERE status = 'INACTIVE'"))
    op.execute(sa.text("ALTER TABLE personas MODIFY COLUMN status ENUM('PENDING','READY','FAILED') NOT NULL"))


def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE personas MODIFY COLUMN status ENUM('CREATING','ACTIVE','INACTIVE','PENDING','READY','FAILED') NOT NULL"))
    op.execute(sa.text("UPDATE personas SET status = 'CREATING' WHERE status = 'PENDING'"))
    op.execute(sa.text("UPDATE personas SET status = 'ACTIVE' WHERE status = 'READY'"))
    op.execute(sa.text("UPDATE personas SET status = 'INACTIVE' WHERE status = 'FAILED'"))
    op.execute(sa.text("ALTER TABLE personas MODIFY COLUMN status ENUM('CREATING','ACTIVE','INACTIVE') NOT NULL"))

    op.drop_column('persona_voice_profiles', 'metadata')
    op.drop_column('personas', 'system_prompt')
    op.drop_column('personas', 'memory_summary')
    op.drop_column('personas', 'persona_name')
