"""align reports enum columns with model

Revision ID: 9830415dacb7
Revises: c8f1d4a7b9e2
Create Date: 2026-05-14 20:21:22.700498

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9830415dacb7'
down_revision = 'c8f1d4a7b9e2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guardrail: fail early if unexpected values exist in legacy VARCHAR columns.
    bind = op.get_bind()
    invalid_target_type = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM reports
            WHERE target_type NOT IN (
                'PERSONA', 'PERSONA_CHAT', 'PERSONA_MESSAGE', 'STORYBOOK', 'SHARE_LINK', 'TARGET', 'USER'
            )
            """
        )
    ).scalar_one()
    invalid_reason_type = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM reports
            WHERE reason_type NOT IN (
                'UNAUTHORIZED_VOICE_USE', 'PRIVACY_VIOLATION', 'HARMFUL_CONTENT',
                'IMPERSONATION', 'COPYRIGHT_OR_RIGHTS', 'SPAM', 'OTHER'
            )
            """
        )
    ).scalar_one()
    invalid_status = bind.execute(
        sa.text(
            """
            SELECT COUNT(*) FROM reports
            WHERE status NOT IN ('PENDING', 'REVIEWING', 'RESOLVED', 'REJECTED', 'ACTION_TAKEN')
            """
        )
    ).scalar_one()

    if invalid_target_type or invalid_reason_type or invalid_status:
        raise RuntimeError(
            "Cannot migrate reports enum columns: unexpected legacy values detected. "
            "Please normalize reports.target_type/reason_type/status first."
        )

    op.alter_column('reports', 'target_type',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               type_=sa.Enum('PERSONA', 'PERSONA_CHAT', 'PERSONA_MESSAGE', 'STORYBOOK', 'SHARE_LINK', 'TARGET', 'USER', name='reporttargettype'),
               existing_nullable=False)
    op.alter_column('reports', 'reason_type',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               type_=sa.Enum('UNAUTHORIZED_VOICE_USE', 'PRIVACY_VIOLATION', 'HARMFUL_CONTENT', 'IMPERSONATION', 'COPYRIGHT_OR_RIGHTS', 'SPAM', 'OTHER', name='reportreasontype'),
               existing_nullable=False)
    op.alter_column('reports', 'status',
               existing_type=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               type_=sa.Enum('PENDING', 'REVIEWING', 'RESOLVED', 'REJECTED', 'ACTION_TAKEN', name='reportstatus'),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('reports', 'status',
               existing_type=sa.Enum('PENDING', 'REVIEWING', 'RESOLVED', 'REJECTED', 'ACTION_TAKEN', name='reportstatus'),
               type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               existing_nullable=False)
    op.alter_column('reports', 'reason_type',
               existing_type=sa.Enum('UNAUTHORIZED_VOICE_USE', 'PRIVACY_VIOLATION', 'HARMFUL_CONTENT', 'IMPERSONATION', 'COPYRIGHT_OR_RIGHTS', 'SPAM', 'OTHER', name='reportreasontype'),
               type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               existing_nullable=False)
    op.alter_column('reports', 'target_type',
               existing_type=sa.Enum('PERSONA', 'PERSONA_CHAT', 'PERSONA_MESSAGE', 'STORYBOOK', 'SHARE_LINK', 'TARGET', 'USER', name='reporttargettype'),
               type_=mysql.VARCHAR(collation='utf8mb4_unicode_ci', length=50),
               existing_nullable=False)

