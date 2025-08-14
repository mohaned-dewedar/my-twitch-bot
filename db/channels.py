from db.database import Database
from typing import Optional

async def add_channel(twitch_channel_id: str, name: str, tier: Optional[int] = None):
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        if tier is not None:
            await conn.execute("""
                INSERT INTO channels (twitch_channel_id, name, tier)
                VALUES ($1, $2, $3)
                ON CONFLICT (twitch_channel_id) DO UPDATE
                SET name = EXCLUDED.name, tier = EXCLUDED.tier
            """, twitch_channel_id, name, tier)
        else:
            await conn.execute("""
                INSERT INTO channels (twitch_channel_id, name)
                VALUES ($1, $2)
                ON CONFLICT (twitch_channel_id) DO UPDATE
                SET name = EXCLUDED.name
            """, twitch_channel_id, name)


async def get_channel_id(twitch_channel_id: str) -> int | None:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM channels WHERE twitch_channel_id = $1
        """, twitch_channel_id)
        return row['id'] if row else None
    

