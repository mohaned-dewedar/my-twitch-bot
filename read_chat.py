import os
from twitchio.ext import commands
from dotenv import load_dotenv

load_dotenv()  

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
        print(f"✅ Logged in as {self._user.name}")

    async def event_message(self, message):
        print(f"[{message.channel.name}] {message.author.name}: {message.content}")

bot = Bot()
bot.run()
