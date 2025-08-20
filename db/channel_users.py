from db.database import Database
from typing import Optional

async def get_or_create_channel_user(channel_id: int, user_id: int) -> dict:
    """Get or create a channel_users record for tracking user stats"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        # Try to get existing record
        result = await conn.fetchrow("""
            SELECT * FROM channel_users 
            WHERE channel_id = $1 AND user_id = $2
        """, channel_id, user_id)
        
        if result:
            # Update last_seen timestamp
            await conn.execute("""
                UPDATE channel_users 
                SET last_seen = CURRENT_TIMESTAMP 
                WHERE channel_id = $1 AND user_id = $2
            """, channel_id, user_id)
            return dict(result)
        else:
            # Create new record
            result = await conn.fetchrow("""
                INSERT INTO channel_users (channel_id, user_id)
                VALUES ($1, $2)
                RETURNING *
            """, channel_id, user_id)
            return dict(result)

async def update_user_stats(channel_id: int, user_id: int, is_correct: bool):
    """Update user statistics after answering a question"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        # Ensure channel_user record exists
        await get_or_create_channel_user(channel_id, user_id)
        
        if is_correct:
            # Correct answer: increment stats and streak
            await conn.execute("""
                UPDATE channel_users 
                SET total_questions = total_questions + 1,
                    correct_answers = correct_answers + 1,
                    streak = streak + 1,
                    best_streak = GREATEST(best_streak, streak + 1),
                    last_seen = CURRENT_TIMESTAMP
                WHERE channel_id = $1 AND user_id = $2
            """, channel_id, user_id)
        else:
            # Wrong answer: increment total, reset streak
            await conn.execute("""
                UPDATE channel_users 
                SET total_questions = total_questions + 1,
                    streak = 0,
                    last_seen = CURRENT_TIMESTAMP
                WHERE channel_id = $1 AND user_id = $2
            """, channel_id, user_id)

async def get_channel_user_rank(channel_id: int, user_id: int) -> Optional[int]:
    """Get user's current rank in the channel leaderboard"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            WITH ranked_users AS (
                SELECT user_id, 
                       ROW_NUMBER() OVER (ORDER BY correct_answers DESC, 
                                         CASE WHEN total_questions > 0 
                                              THEN correct_answers::float / total_questions::float 
                                              ELSE 0 
                                         END DESC) as rank
                FROM channel_users 
                WHERE channel_id = $1 AND total_questions > 0
            )
            SELECT rank FROM ranked_users WHERE user_id = $2
        """, channel_id, user_id)
        
        return result['rank'] if result else None

async def get_top_streaks(channel_id: int, limit: int = 5):
    """Get users with the highest streaks in a channel"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.twitch_username, cu.best_streak, cu.streak as current_streak
            FROM channel_users cu
            JOIN users u ON cu.user_id = u.id
            WHERE cu.channel_id = $1 AND cu.best_streak > 0
            ORDER BY cu.best_streak DESC, cu.correct_answers DESC
            LIMIT $2
        """, channel_id, limit)

async def reset_user_streak(channel_id: int, user_id: int):
    """Reset user's current streak (used when giving up or timing out)"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE channel_users 
            SET streak = 0, last_seen = CURRENT_TIMESTAMP
            WHERE channel_id = $1 AND user_id = $2
        """, channel_id, user_id)

async def get_channel_stats_summary(channel_id: int):
    """Get overall statistics for a channel"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_users,
                SUM(total_questions) as total_questions_answered,
                SUM(correct_answers) as total_correct_answers,
                MAX(best_streak) as highest_streak,
                AVG(CASE WHEN total_questions > 0 
                         THEN correct_answers::float / total_questions::float 
                         ELSE 0 
                    END) as average_accuracy
            FROM channel_users 
            WHERE channel_id = $1 AND total_questions > 0
        """, channel_id)
        
        return dict(result) if result else None