"""ai interview sessions mvp

Revision ID: e3b8f2a6c1d5
Revises: d2a7c4b9e8f1
Create Date: 2026-05-09 04:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3b8f2a6c1d5'
down_revision = 'd2a7c4b9e8f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ai_interview_sessions', sa.Column('session_type', sa.String(length=32), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('status', sa.String(length=32), nullable=False, server_default='IN_PROGRESS'))
    op.add_column('ai_interview_sessions', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE ai_interview_sessions
            SET session_type = CASE
                WHEN interview_type = 'TARGET_PROFILE' THEN 'TARGET_PROFILE'
                WHEN interview_type = 'target_profile' THEN 'TARGET_PROFILE'
                WHEN interview_type = 'PHOTO_MEMORY' THEN 'PHOTO_MEMORY'
                WHEN interview_type = 'photo_memory' THEN 'PHOTO_MEMORY'
                ELSE 'SELF_STORY'
            END
            """
        )
    )
    op.alter_column('ai_interview_sessions', 'session_type', existing_type=sa.String(length=32), nullable=False)

    op.drop_column('ai_interview_sessions', 'current_question')
    op.drop_column('ai_interview_sessions', 'user_answer')
    op.drop_column('ai_interview_sessions', 'follow_up_question')
    op.drop_column('ai_interview_sessions', 'is_completed')
    op.drop_column('ai_interview_sessions', 'is_deleted')
    op.drop_column('ai_interview_sessions', 'interview_type')

    op.create_table(
        'ai_interview_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=100), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['ai_interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_interview_questions_id'), 'ai_interview_questions', ['id'], unique=False)
    op.create_index(op.f('ix_ai_interview_questions_session_id'), 'ai_interview_questions', ['session_id'], unique=False)

    op.create_table(
        'ai_interview_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('answer_audio_path', sa.String(length=512), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['question_id'], ['ai_interview_questions.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['ai_interview_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ai_interview_answers_id'), 'ai_interview_answers', ['id'], unique=False)
    op.create_index(op.f('ix_ai_interview_answers_question_id'), 'ai_interview_answers', ['question_id'], unique=False)
    op.create_index(op.f('ix_ai_interview_answers_session_id'), 'ai_interview_answers', ['session_id'], unique=False)

    op.alter_column(
        'ai_interview_sessions',
        'session_type',
        existing_type=sa.String(length=32),
        type_=sa.Enum('TARGET_PROFILE', 'PHOTO_MEMORY', 'SELF_STORY', name='interviewtype'),
        existing_nullable=False,
    )
    op.alter_column(
        'ai_interview_sessions',
        'status',
        existing_type=sa.String(length=32),
        type_=sa.Enum('IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='interviewstatus'),
        existing_nullable=False,
        server_default=None,
    )


def downgrade() -> None:
    op.alter_column(
        'ai_interview_sessions',
        'status',
        existing_type=sa.Enum('IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='interviewstatus'),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
    op.alter_column(
        'ai_interview_sessions',
        'session_type',
        existing_type=sa.Enum('TARGET_PROFILE', 'PHOTO_MEMORY', 'SELF_STORY', name='interviewtype'),
        type_=sa.String(length=32),
        existing_nullable=False,
    )

    op.drop_index(op.f('ix_ai_interview_answers_session_id'), table_name='ai_interview_answers')
    op.drop_index(op.f('ix_ai_interview_answers_question_id'), table_name='ai_interview_answers')
    op.drop_index(op.f('ix_ai_interview_answers_id'), table_name='ai_interview_answers')
    op.drop_table('ai_interview_answers')
    op.drop_index(op.f('ix_ai_interview_questions_session_id'), table_name='ai_interview_questions')
    op.drop_index(op.f('ix_ai_interview_questions_id'), table_name='ai_interview_questions')
    op.drop_table('ai_interview_questions')

    op.add_column('ai_interview_sessions', sa.Column('interview_type', sa.String(length=32), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('ai_interview_sessions', sa.Column('is_completed', sa.Boolean(), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('follow_up_question', sa.Text(), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('user_answer', sa.Text(), nullable=True))
    op.add_column('ai_interview_sessions', sa.Column('current_question', sa.Text(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE ai_interview_sessions
            SET interview_type = CASE
                WHEN session_type = 'TARGET_PROFILE' THEN 'TARGET_PROFILE'
                WHEN session_type = 'PHOTO_MEMORY' THEN 'PHOTO_MEMORY'
                ELSE 'PERSONA_CREATION'
            END
            """
        )
    )
    op.alter_column('ai_interview_sessions', 'interview_type', existing_type=sa.String(length=32), nullable=False)

    op.drop_column('ai_interview_sessions', 'deleted_at')
    op.drop_column('ai_interview_sessions', 'status')
    op.drop_column('ai_interview_sessions', 'title')
    op.drop_column('ai_interview_sessions', 'session_type')
