import asyncio
from db.database import Database
from db.channels import add_channel
from config import DATABASE_URL

async def main():
    await Database.init(DATABASE_URL)

    await add_channel("streamer_123", "StreamerName")

    await Database.close()

if __name__ == "__main__":
    asyncio.run(main())
