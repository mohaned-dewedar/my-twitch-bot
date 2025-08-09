import websockets
import asyncio
from config import TWITCH_BOT_NAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL
from twitch.message_parser import parse_privmsg
from llm.ollama_worker import OllamaWorkerQueue
from data.data_loader import SmiteDataStore 
from trivia.types import ApiTriviaHandler, SmiteTriviaHandler
from trivia.manager import TriviaManager
from typing import Optional





class IRCClient:
    def __init__(self):
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.buffer = []
        self.ollama_queue = OllamaWorkerQueue()
        asyncio.create_task(self.ollama_queue.start())
        
        
        self.api_handler = ApiTriviaHandler(use_custom=False)

        self.smite_store = SmiteDataStore()
        if not self.smite_store.load_data():
            print("⚠️ Warning: Failed to load Smite data.")
        else:
            print("✅ Smite data loaded successfully!")

        # Initialize trivia components
        self.manager = TriviaManager()
        self.smite_handler = SmiteTriviaHandler(self.smite_store)  

    async def connect(self):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"PASS {TWITCH_OAUTH_TOKEN}")
            await websocket.send(f"NICK {TWITCH_BOT_NAME}")
            await websocket.send(f"JOIN #{TWITCH_CHANNEL}")
            print(f"✅ Connected to #{TWITCH_CHANNEL} as {TWITCH_BOT_NAME}")

            while True:
                try:
                    msg = await websocket.recv()
                    print(">>", msg.strip())

                    if msg.startswith("PING"):
                        await websocket.send("PONG :tmi.twitch.tv")
                        continue

                    parsed = parse_privmsg(msg)
                    if parsed:
                        self.buffer.append(parsed)
                        await self.handle_message(parsed, websocket)

                except websockets.exceptions.ConnectionClosed:
                    print("⚠️ Disconnected. Reconnecting...")
                    break

    async def handle_message(self, parsed, websocket):
        username = parsed['user']
        message = parsed['message']
        response = self.handle_trivia_command(message, username)
        if response:
            await self.send_message(websocket, response)

    def format_multiple_choice_question(self, q: dict) -> str:
        answers = q.get("all_answers", [])
        # Use emojis and readable formatting for Twitch chat (no \n)
        formatted = " ".join([f"{chr(0x1F1E6+i)} {ans}" for i, ans in enumerate(answers)])  # 🇦 🇧 🇨 ...
        return f"🎲 {q['question']} | {formatted} | Category: {q.get('category', 'Unknown')}"

    def handle_trivia_command(self, message: str, username: str) -> Optional[str]:
        msg = message.lower().strip()

        if msg.startswith("!trivia-help"):
            return self.manager.get_help()

        elif msg.startswith("!giveup"):
            return self.manager.end_trivia()

        elif msg.startswith("!answer"):
            guess = message[len("!answer"):].strip()
            return self.manager.submit_answer(guess, username)

        elif msg.startswith("!trivia smite"):
            # Smite trivia already uses formatted output
            return self.manager.start_trivia(self.smite_handler)

        elif msg.startswith("!trivia"):
            # API trivia: format question with options for chat
            result = self.manager.start_trivia(self.api_handler)
            # Try to get the current question and format if possible
            q = self.api_handler.get_question() if hasattr(self.api_handler, 'get_question') else None
            if q and q.get("all_answers"):
                return self.format_multiple_choice_question(q)
            return result

        return None


    async def send_message(self, websocket, message: str):
        max_len = 450
        if len(message) > max_len:
            message = message[:max_len - 3] + "..."
        print(f"📤 Sending: {message[:60]}...")
        await websocket.send(f"PRIVMSG #{TWITCH_CHANNEL} :{message.strip()}")
