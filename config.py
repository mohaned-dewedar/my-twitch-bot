import os
from dotenv import load_dotenv

load_dotenv()

TWITCH_BOT_NAME = os.getenv("TWITCH_BOT_NAME", "yoru_bot_name")
TWITCH_OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN", "oauth:your_token_here")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "your_channel_name")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://trivia:trivia-password@localhost:5432/trivia")
