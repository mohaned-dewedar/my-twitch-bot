from db.database import Database

async def get_or_create_user(twitch_username: str) -> int:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO users (twitch_username)
            VALUES ($1)
            ON CONFLICT (twitch_username) DO NOTHING
            RETURNING id
        """, twitch_username)

        if row:
            return row['id']

        row = await conn.fetchrow("SELECT id FROM users WHERE twitch_username = $1", twitch_username)
        return row['id']
