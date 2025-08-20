"""enhance_schema_for_proper_leaderboards

Revision ID: 25355730f24f
Revises: 2346220c062c
Create Date: 2025-08-20 05:12:31.569521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25355730f24f'
down_revision: Union[str, Sequence[str], None] = '2346220c062c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add twitch_channel_id column to channels table if it doesn't exist
    op.add_column('channels', sa.Column('twitch_channel_id', sa.String(255), nullable=True))
    
    # Add user_id and channel_id columns to attempts table for direct user tracking
    op.add_column('attempts', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('attempts', sa.Column('channel_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key('fk_attempts_user_id', 'attempts', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_attempts_channel_id', 'attempts', 'channels', ['channel_id'], ['id'], ondelete='CASCADE')
    
    # Create channel_users table for optimized leaderboard tracking
    op.create_table('channel_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_seen', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('total_questions', sa.Integer(), server_default='0', nullable=True),
        sa.Column('correct_answers', sa.Integer(), server_default='0', nullable=True),
        sa.Column('streak', sa.Integer(), server_default='0', nullable=True),
        sa.Column('best_streak', sa.Integer(), server_default='0', nullable=True),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_id', 'user_id', name='uq_channel_users_channel_user')
    )
    
    # Create performance indexes
    op.create_index('idx_attempts_user_channel', 'attempts', ['user_id', 'channel_id'])
    op.create_index('idx_attempts_correct_answers', 'attempts', ['is_correct'], postgresql_where=sa.text('is_correct = true'))
    op.create_index('idx_attempts_session', 'attempts', ['session_id'])
    op.create_index('idx_attempts_question', 'attempts', ['question_id'])
    op.create_index('idx_sessions_channel', 'sessions', ['channel_id'])
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_questions_category', 'questions', ['category'])
    op.create_index('idx_questions_bank', 'questions', ['bank_id'])
    op.create_index('idx_channel_users_stats', 'channel_users', ['channel_id', 'correct_answers'])
    op.create_index('idx_channels_twitch_id', 'channels', ['twitch_channel_id'])
    
    # Make twitch_channel_id unique and not null after data migration
    op.execute("UPDATE channels SET twitch_channel_id = COALESCE(twitch_channel_id, 'channel_' || id::text) WHERE twitch_channel_id IS NULL")
    op.alter_column('channels', 'twitch_channel_id', nullable=False)
    op.create_unique_constraint('uq_channels_twitch_channel_id', 'channels', ['twitch_channel_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_channels_twitch_id')
    op.drop_index('idx_channel_users_stats')
    op.drop_index('idx_questions_bank')
    op.drop_index('idx_questions_category')
    op.drop_index('idx_sessions_status')
    op.drop_index('idx_sessions_channel')
    op.drop_index('idx_attempts_question')
    op.drop_index('idx_attempts_session')
    op.drop_index('idx_attempts_correct_answers')
    op.drop_index('idx_attempts_user_channel')
    
    # Drop channel_users table
    op.drop_table('channel_users')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_attempts_channel_id', 'attempts', type_='foreignkey')
    op.drop_constraint('fk_attempts_user_id', 'attempts', type_='foreignkey')
    
    # Remove columns from attempts
    op.drop_column('attempts', 'channel_id')
    op.drop_column('attempts', 'user_id')
    
    # Remove twitch_channel_id constraint and column
    op.drop_constraint('uq_channels_twitch_channel_id', 'channels', type_='unique')
    op.drop_column('channels', 'twitch_channel_id')
