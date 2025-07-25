import websockets
import asyncio
from config import TWITCH_BOT_NAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL
from twitch.message_parser import parse_privmsg
from llm.ollama_worker import OllamaWorkerQueue
from data.data_loader import SmiteDataLoader
from llm.trivia_handler import TriviaHandler, GeneralTriviaCache
from typing import Optional


class TriviaSession:
    def __init__(self):
        self.active = False
        self.question = None
        self.correct_answer = None
        self.answers = []
        self.category = None
        self.qtype = None  # 'multiple', 'boolean', or 'smite'

    def start(self, q: dict, qtype: str):
        self.active = True
        self.qtype = qtype
        self.question = q.get("question")
        self.correct_answer = q.get("correct_answer")
        self.answers = q.get("all_answers", [])
        self.category = q.get("category", "General")

    def end(self):
        self.__init__()  # Clean reset

    def is_active(self):
        return self.active



class IRCClient:
    def __init__(self):
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.buffer = []
        self.ollama_queue = OllamaWorkerQueue()
        asyncio.create_task(self.ollama_queue.start())

        self.session = TriviaSession()
        self.data_loader = SmiteDataLoader()
        self.trivia_handler = TriviaHandler(self.data_loader)
        self.general_cache = GeneralTriviaCache()

        if not self.data_loader.load_data():
            print("Warning: Failed to load Smite data. Trivia functionality will not work.")
        else:
            print("Smite data loaded successfully!")

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

    def check_answer(self, guess: str, username: str) -> str:
   
        if self.session.qtype == "smite":
            match = self.trivia_handler.data_loader.fuzzy_match_god(guess)
            if match and match.lower() == self.session.correct_answer.lower():
                msg = f"🎉 @{username} got it right! The answer was: {self.session.correct_answer}"
                self.session.end()
            else:
                msg = f"❌ @{username}, that's not correct. Try again!"
            return msg

        else:
            
            correct = self.session.correct_answer.strip().lower()
            given = guess.strip().lower()

            if given == correct or given in correct:
                response = f"🎉 @{username} got it right! The answer was: {self.session.correct_answer}"
                self.session.end()
            else:
                response = f"❌ @{username}, that's not correct. Try again!"
            return response

    def format_multiple_choice_question(self, q: dict) -> str:
        answers = q.get("all_answers", [])
        formatted = "\n".join(f"{chr(65+i)}. {ans}" for i, ans in enumerate(answers))
        return f"🎲 {q['question']}\n{formatted} (Category: {q['category']})"

    def handle_trivia_command(self, message: str, username: str) -> Optional[str]:
        msg = message.lower()

        if msg.startswith("!trivia-help"):
            return self.trivia_handler.get_help_message()

        elif msg.startswith("!answer"):
            if not self.session.is_active():
                return "❌ No active trivia. Start one with !trivia"
            guess = message[len("!answer"):].strip()
            return self.check_answer(guess, username)

        elif msg.startswith("!trivia category"):
            parts = message.split(maxsplit=2)
            if len(parts) < 3:
                return "⚠️ Please specify a category after !trivia category."
            category = parts[2].strip()
            q = self.general_cache.get_multiple_choice(category=category)
            self.session.start(q, "multiple")
            return self.format_multiple_choice_question(q)

        elif msg.startswith("!trivia smite"):
            if self.session.is_active():
                return "⚠️ A trivia session is already active. Use !answer to respond."

            q = self.trivia_handler.get_smite_trivia_question()
            if not q:
                return "⚠️ Could not start a Smite trivia round."

            self.session.start(q, "smite")
            return f"🎯 TRIVIA TIME! {q['question']} Type !answer [god name] to guess!"

        elif msg.startswith("!trivia"):
            if self.session.is_active():
                return "⚠️ There's already an active trivia question. Use !answer [your guess]"
            q = self.general_cache.get_multiple_choice()
            self.session.start(q, "multiple")
            return self.format_multiple_choice_question(q)

        return None

    async def send_message(self, websocket, message: str):
        message = message.strip()
        max_len = 450
        if len(message) > max_len:
            message = message[:max_len - 3] + "..."
        print(f"📤 Sending: {message[:60]}...")
        await websocket.send(f"PRIVMSG #{TWITCH_CHANNEL} :{message}")
