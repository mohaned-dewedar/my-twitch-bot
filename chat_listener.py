import asyncio
from twitch.irc_client import IRCClient

async def main():
    client = IRCClient()
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
