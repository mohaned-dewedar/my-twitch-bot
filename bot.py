import asyncio
import logging
import os
from dotenv import load_dotenv
from twitchio.ext import commands
load_dotenv()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("Bot")

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            client_id=os.getenv("TWITCH_CLIENT_ID"),
            client_secret=os.getenv("TWITCH_CLIENT_SECRET"),
            bot_id=os.getenv("TWITCH_BOT_ID"),
            owner_id=None,
            prefix="!",
            initial_channels=[os.getenv("TWITCH_CHANNEL")],
            token=os.getenv("TWITCH_OAUTH_TOKEN"),
        )

    async def event_ready(self):
        LOGGER.info(f"Bot is online as {self._user.name}")


    @commands.command()
    async def hi(self, ctx: commands.Context):
        await ctx.reply(f"Hello {ctx.author.name}!")

    @commands.command()
    async def echo(self, ctx: commands.Context, *, msg: str):
        await ctx.send(msg)

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
