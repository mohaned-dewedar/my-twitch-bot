import os
from dotenv import load_dotenv

load_dotenv()

TWITCH_USERNAME = os.getenv("TWITCH_USERNAME", "thecherryo_bot")
TWITCH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN", "oauth:your_token_here")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "thecherryo")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
