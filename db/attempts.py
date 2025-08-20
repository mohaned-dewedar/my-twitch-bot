from db.database import Database
from db.channel_users import update_user_stats

async def create_attempt(session_id: int, question_id: int, user_id: int, 
                        channel_id: int, user_answer: str, is_correct: bool) -> int:
    """Create a new attempt record and update user stats"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        # Create the attempt record
        result = await conn.fetchrow("""
            INSERT INTO attempts (session_id, question_id, user_id, channel_id, user_answer, is_correct)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """, session_id, question_id, user_id, channel_id, user_answer, is_correct)
        
        attempt_id = result['id']
        
        # Update user statistics in channel_users table
        await update_user_stats(channel_id, user_id, is_correct)
        
        return attempt_id

async def get_user_attempts(user_id: int, channel_id: int, limit: int = 20):
    """Get recent attempts for a user in a specific channel"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT a.id, a.user_answer, a.is_correct, a.created_at,
                   q.question, q.answer as correct_answer, q.category
            FROM attempts a
            JOIN questions q ON a.question_id = q.id
            WHERE a.user_id = $1 AND a.channel_id = $2
            ORDER BY a.created_at DESC
            LIMIT $3
        """, user_id, channel_id, limit)

async def get_session_attempts(session_id: int):
    """Get all attempts for a specific trivia session"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT a.id, a.user_answer, a.is_correct, a.created_at,
                   u.twitch_username, q.question, q.answer as correct_answer
            FROM attempts a
            JOIN users u ON a.user_id = u.id
            JOIN questions q ON a.question_id = q.id
            WHERE a.session_id = $1
            ORDER BY a.created_at ASC
        """, session_id)

async def get_question_attempts(question_id: int, channel_id: int):
    """Get all attempts for a specific question in a channel"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT a.id, a.user_answer, a.is_correct, a.created_at,
                   u.twitch_username
            FROM attempts a
            JOIN users u ON a.user_id = u.id
            WHERE a.question_id = $1 AND a.channel_id = $2
            ORDER BY a.created_at ASC
        """, question_id, channel_id)

async def get_attempt_stats(channel_id: int, days: int = 7):
    """Get attempt statistics for a channel over the past N days"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_attempts,
                COUNT(*) FILTER (WHERE is_correct = TRUE) as correct_attempts,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT question_id) as unique_questions,
                CASE WHEN COUNT(*) > 0 
                     THEN ROUND((COUNT(*) FILTER (WHERE is_correct = TRUE)::float / COUNT(*)::float) * 100, 1) 
                     ELSE 0 
                END as overall_accuracy
            FROM attempts 
            WHERE channel_id = $1 
            AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days, channel_id)
        
        return dict(result) if result else None

async def check_duplicate_attempt(session_id: int, question_id: int, user_id: int) -> bool:
    """Check if user has already answered this question in this session"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT id FROM attempts 
            WHERE session_id = $1 AND question_id = $2 AND user_id = $3
            LIMIT 1
        """, session_id, question_id, user_id)
        
        return result is not None