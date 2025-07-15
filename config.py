import os
from dotenv import load_dotenv

load_dotenv()

TWITCH_USERNAME = os.getenv("TWITCH_USERNAME", "yoru_bot_name")
TWITCH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN", "oauth:your_token_here")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "your_channel_name")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
