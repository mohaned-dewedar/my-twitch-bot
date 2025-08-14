from db.database import Database
from typing import Optional

async def start_session(channel_id: int, user_id: int) -> int:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO sessions (channel_id, user_id)
            VALUES ($1, $2)
            RETURNING id
        """, channel_id, user_id)
        return row['id']

async def end_session(session_id: int):
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE sessions
            SET end_time = CURRENT_TIMESTAMP, status = 'completed'
            WHERE id = $1
        """, session_id)

async def get_active_session(channel_id: int) -> Optional[int]:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM sessions
            WHERE channel_id = $1 AND status = 'active'
            ORDER BY start_time DESC
            LIMIT 1
        """, channel_id)
        return row['id'] if row else None
