"""Fix double counting - enhance trigger with streak logic

Revision ID: 9eced53a46e1
Revises: d464c704f3d6
Create Date: 2025-09-05 15:13:18.721006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eced53a46e1'
down_revision: Union[str, Sequence[str], None] = 'd464c704f3d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix double counting by enhancing database trigger with streak logic."""
    # Update the trigger function to include streak calculations
    # This prevents double counting that was happening when both manual update_user_stats()
    # and the database trigger were updating the same stats
    op.execute("""
        -- Function to update user stats including streaks
        -- This function runs automatically after each attempt is inserted
        -- It handles: total stats, question-type stats, and streak calculations
        CREATE OR REPLACE FUNCTION update_channel_user_stats()
        RETURNS TRIGGER AS $$
        DECLARE
            q_type VARCHAR(50);
        BEGIN
            -- Get question type for type-specific stat tracking
            SELECT question_type INTO q_type FROM questions WHERE id = NEW.question_id;
            
            -- Update or insert channel_users record with comprehensive stats
            INSERT INTO channel_users (
                channel_id, user_id, total_questions, correct_answers, 
                current_streak, best_streak, last_seen
            )
            VALUES (
                NEW.channel_id, NEW.user_id, 1, 
                CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
                CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,  -- Start streak at 1 if correct, 0 if wrong
                CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,  -- Set best_streak to current_streak
                NEW.created_at
            )
            ON CONFLICT (channel_id, user_id) 
            DO UPDATE SET
                -- Basic stats
                total_questions = channel_users.total_questions + 1,
                correct_answers = channel_users.correct_answers + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
                last_seen = NEW.created_at,
                
                -- Streak logic: if correct, increment; if wrong, reset to 0
                current_streak = CASE 
                    WHEN NEW.is_correct THEN channel_users.current_streak + 1 
                    ELSE 0 
                END,
                
                -- Best streak: keep the maximum between current best and new current streak
                best_streak = CASE 
                    WHEN NEW.is_correct THEN GREATEST(channel_users.best_streak, channel_users.current_streak + 1)
                    ELSE channel_users.best_streak 
                END,
                
                -- Question-type specific stats (MCQ, True/False, Open-ended)
                mcq_total = CASE WHEN q_type = 'multiple_choice' THEN channel_users.mcq_total + 1 ELSE channel_users.mcq_total END,
                mcq_correct = CASE WHEN q_type = 'multiple_choice' AND NEW.is_correct THEN channel_users.mcq_correct + 1 ELSE channel_users.mcq_correct END,
                tf_total = CASE WHEN q_type = 'true_false' THEN channel_users.tf_total + 1 ELSE channel_users.tf_total END,
                tf_correct = CASE WHEN q_type = 'true_false' AND NEW.is_correct THEN channel_users.tf_correct + 1 ELSE channel_users.tf_correct END,
                open_total = CASE WHEN q_type = 'open_ended' THEN channel_users.open_total + 1 ELSE channel_users.open_total END,
                open_correct = CASE WHEN q_type = 'open_ended' AND NEW.is_correct THEN channel_users.open_correct + 1 ELSE channel_users.open_correct END;
                
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Downgrade to previous trigger function without streak logic."""
    # Revert to the original trigger function that doesn't handle streaks
    op.execute("""
        CREATE OR REPLACE FUNCTION update_channel_user_stats()
        RETURNS TRIGGER AS $$
        DECLARE
            q_type VARCHAR(50);
        BEGIN
            -- Get question type
            SELECT question_type INTO q_type FROM questions WHERE id = NEW.question_id;
            
            -- Update or insert channel_users record
            INSERT INTO channel_users (channel_id, user_id, total_questions, correct_answers, last_seen)
            VALUES (NEW.channel_id, NEW.user_id, 1, CASE WHEN NEW.is_correct THEN 1 ELSE 0 END, NEW.created_at)
            ON CONFLICT (channel_id, user_id) 
            DO UPDATE SET
                total_questions = channel_users.total_questions + 1,
                correct_answers = channel_users.correct_answers + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
                last_seen = NEW.created_at,
                -- Update type-specific stats
                mcq_total = CASE WHEN q_type = 'multiple_choice' THEN channel_users.mcq_total + 1 ELSE channel_users.mcq_total END,
                mcq_correct = CASE WHEN q_type = 'multiple_choice' AND NEW.is_correct THEN channel_users.mcq_correct + 1 ELSE channel_users.mcq_correct END,
                tf_total = CASE WHEN q_type = 'true_false' THEN channel_users.tf_total + 1 ELSE channel_users.tf_total END,
                tf_correct = CASE WHEN q_type = 'true_false' AND NEW.is_correct THEN channel_users.tf_correct + 1 ELSE channel_users.tf_correct END,
                open_total = CASE WHEN q_type = 'open_ended' THEN channel_users.open_total + 1 ELSE channel_users.open_total END,
                open_correct = CASE WHEN q_type = 'open_ended' AND NEW.is_correct THEN channel_users.open_correct + 1 ELSE channel_users.open_correct END;
                
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
