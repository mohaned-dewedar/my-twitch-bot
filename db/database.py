import asyncpg
import asyncio

class Database:
    _pool = None

    @classmethod
    async def init(cls, dsn):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(dsn)
        return cls._pool

    @classmethod
    async def get_pool(cls):
        if cls._pool is None:
            raise Exception("Database pool not initialized. Call Database.init() first.")
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
