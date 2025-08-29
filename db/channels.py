from db.database import Database
from typing import Optional

async def add_channel(twitch_channel_id: str, name: str, tier: Optional[int] = None):
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        # Check for existing channel with case-insensitive match
        existing_row = await conn.fetchrow("""
            SELECT id FROM channels WHERE LOWER(twitch_channel_id) = LOWER($1)
        """, twitch_channel_id)
        
        if existing_row:
            # Update existing channel
            if tier is not None:
                await conn.execute("""
                    UPDATE channels SET name = $2, tier = $3 WHERE id = $1
                """, existing_row['id'], name, tier)
            else:
                await conn.execute("""
                    UPDATE channels SET name = $2 WHERE id = $1
                """, existing_row['id'], name)
        else:
            # Insert new channel
            if tier is not None:
                await conn.execute("""
                    INSERT INTO channels (twitch_channel_id, name, tier)
                    VALUES ($1, $2, $3)
                """, twitch_channel_id, name, tier)
            else:
                await conn.execute("""
                    INSERT INTO channels (twitch_channel_id, name)
                    VALUES ($1, $2)
                """, twitch_channel_id, name)


async def get_channel_id(twitch_channel_id: str) -> int | None:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM channels WHERE LOWER(twitch_channel_id) = LOWER($1)
        """, twitch_channel_id)
        return row['id'] if row else None
    

