"""deletion requests mvp

Revision ID: d8a4b7c1e6f9
Revises: c7f2a8d5e9b3
Create Date: 2026-05-09 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'd8a4b7c1e6f9'
down_revision = 'c7f2a8d5e9b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('deletion_requests', 'item_type',
                    existing_type=mysql.ENUM('PHOTO', 'VOICE', 'MESSAGE', 'STORYBOOK', 'PERSONA', 'CHAT'),
                    type_=sa.String(length=64),
                    new_column_name='target_type',
                    existing_nullable=False)
    op.alter_column('deletion_requests', 'item_id',
                    existing_type=sa.Integer(),
                    new_column_name='target_id',
                    existing_nullable=False)
    op.alter_column('deletion_requests', 'status',
                    existing_type=mysql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'),
                    type_=sa.String(length=32),
                    existing_nullable=False)
    op.execute(
        sa.text(
            """
            UPDATE deletion_requests
            SET target_type = CASE
                WHEN target_type = 'PHOTO' THEN 'PHOTO_MEMORY'
                WHEN target_type = 'VOICE' THEN 'TARGET_MEDIA'
                WHEN target_type = 'MESSAGE' THEN 'PERSONA_MESSAGE'
                WHEN target_type = 'CHAT' THEN 'PERSONA_CHAT'
                ELSE target_type
            END
            """
        )
    )
    op.execute(sa.text("UPDATE deletion_requests SET status = 'REQUESTED' WHERE status IN ('PENDING', 'PROCESSING')"))
    op.add_column('deletion_requests', sa.Column('processed_at', sa.DateTime(), nullable=True))
    op.drop_column('deletion_requests', 'file_paths')
    op.drop_column('deletion_requests', 'is_deleted')
    op.alter_column(
        'deletion_requests',
        'target_type',
        existing_type=sa.String(length=64),
        type_=sa.Enum(
            'TARGET',
            'TARGET_MEDIA',
            'PERSONA',
            'PERSONA_CHAT',
            'PERSONA_MESSAGE',
            'PHOTO_MEMORY',
            'STORYBOOK',
            'SHARE_LINK',
            'MEMORY_GROUP',
            'ACCOUNT',
            name='deletiontargettype',
        ),
        existing_nullable=False,
    )
    op.alter_column(
        'deletion_requests',
        'status',
        existing_type=sa.String(length=32),
        type_=sa.Enum('REQUESTED', 'COMPLETED', 'FAILED', name='deletionstatus'),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column('deletion_requests', 'status',
                    existing_type=sa.Enum('REQUESTED', 'COMPLETED', 'FAILED', name='deletionstatus'),
                    type_=sa.String(length=32),
                    existing_nullable=False)
    op.alter_column('deletion_requests', 'target_type',
                    existing_type=sa.Enum(
                        'TARGET',
                        'TARGET_MEDIA',
                        'PERSONA',
                        'PERSONA_CHAT',
                        'PERSONA_MESSAGE',
                        'PHOTO_MEMORY',
                        'STORYBOOK',
                        'SHARE_LINK',
                        'MEMORY_GROUP',
                        'ACCOUNT',
                        name='deletiontargettype',
                    ),
                    type_=sa.String(length=64),
                    existing_nullable=False)
    op.add_column('deletion_requests', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('deletion_requests', sa.Column('file_paths', sa.String(length=2048), nullable=True))
    op.execute(sa.text("UPDATE deletion_requests SET status = 'COMPLETED' WHERE status = 'COMPLETED'"))
    op.execute(sa.text("UPDATE deletion_requests SET status = 'FAILED' WHERE status = 'FAILED'"))
    op.execute(sa.text("UPDATE deletion_requests SET status = 'PENDING' WHERE status = 'REQUESTED'"))
    op.execute(
        sa.text(
            """
            UPDATE deletion_requests
            SET target_type = CASE
                WHEN target_type = 'PHOTO_MEMORY' THEN 'PHOTO'
                WHEN target_type = 'TARGET_MEDIA' THEN 'VOICE'
                WHEN target_type = 'PERSONA_MESSAGE' THEN 'MESSAGE'
                WHEN target_type = 'PERSONA_CHAT' THEN 'CHAT'
                ELSE target_type
            END
            """
        )
    )
    op.drop_column('deletion_requests', 'processed_at')
    op.alter_column('deletion_requests', 'status',
                    existing_type=sa.String(length=32),
                    type_=mysql.ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'),
                    existing_nullable=False)
    op.alter_column('deletion_requests', 'target_id',
                    existing_type=sa.Integer(),
                    new_column_name='item_id',
                    existing_nullable=False)
    op.alter_column('deletion_requests', 'target_type',
                    existing_type=sa.String(length=64),
                    type_=mysql.ENUM('PHOTO', 'VOICE', 'MESSAGE', 'STORYBOOK', 'PERSONA', 'CHAT'),
                    new_column_name='item_type',
                    existing_nullable=False)
