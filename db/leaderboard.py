from db.database import Database

async def get_leaderboard(channel_id: int, limit: int = 10):
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT u.twitch_username, COUNT(*) AS correct_answers
            FROM attempts a
            JOIN sessions s ON a.session_id = s.id
            JOIN users u ON s.user_id = u.id
            WHERE s.channel_id = $1 AND a.is_correct = TRUE
            GROUP BY u.twitch_username
            ORDER BY correct_answers DESC
            LIMIT $2
        """, channel_id, limit)
