"""add user role column

Revision ID: a9c3d1e8f2b4
Revises: f4c9d7e2a6b1
Create Date: 2026-05-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9c3d1e8f2b4'
down_revision = 'f4c9d7e2a6b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User 모델에 role 컬럼 추가
    op.add_column('users', sa.Column('role', sa.String(length=50), nullable=True))

    # 기본값 설정
    op.execute(sa.text("UPDATE users SET role = 'user' WHERE role IS NULL"))

    # NOT NULL 거제 설정
    op.alter_column('users', 'role', existing_type=sa.String(length=50), nullable=False, server_default='user')


def downgrade() -> None:
    op.drop_column('users', 'role')

