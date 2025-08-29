from db.database import Database

async def get_leaderboard(channel_id: int, limit: int = 10):
    """Get leaderboard for a specific channel using optimized channel_users table"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.twitch_username, cu.correct_answers, cu.total_questions,
                   CASE WHEN cu.total_questions > 0 
                        THEN ROUND(CAST((cu.correct_answers::float / cu.total_questions::float) * 100 AS numeric), 1) 
                        ELSE 0 
                   END as accuracy_pct,
                   cu.best_streak, cu.current_streak
            FROM channel_users cu
            JOIN users u ON cu.user_id = u.id
            WHERE cu.channel_id = $1 AND cu.total_questions > 0
            ORDER BY cu.correct_answers DESC, accuracy_pct DESC
            LIMIT $2
        """, channel_id, limit)

async def get_leaderboard_direct(channel_id: int, limit: int = 10):
    """Fallback method using direct attempts table query"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.twitch_username, 
                   COUNT(*) FILTER (WHERE a.is_correct = TRUE) as correct_answers,
                   COUNT(*) as total_questions,
                   CASE WHEN COUNT(*) > 0 
                        THEN ROUND(CAST((COUNT(*) FILTER (WHERE a.is_correct = TRUE)::float / COUNT(*)::float) * 100 AS numeric), 1) 
                        ELSE 0 
                   END as accuracy_pct
            FROM attempts a
            JOIN users u ON a.user_id = u.id
            WHERE a.channel_id = $1
            GROUP BY u.twitch_username, u.id
            HAVING COUNT(*) > 0
            ORDER BY correct_answers DESC, accuracy_pct DESC
            LIMIT $2
        """, channel_id, limit)

async def get_user_stats(channel_id: int, user_id: int):
    """Get detailed stats for a specific user in a channel"""
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT cu.correct_answers, cu.total_questions, cu.streak, cu.best_streak,
                   CASE WHEN cu.total_questions > 0 
                        THEN ROUND((cu.correct_answers::float / cu.total_questions::float) * 100, 1) 
                        ELSE 0 
                   END as accuracy_pct,
                   cu.first_seen, cu.last_seen
            FROM channel_users cu
            WHERE cu.channel_id = $1 AND cu.user_id = $2
        """, channel_id, user_id)
        return result
