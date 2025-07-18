import websockets
import asyncio
from config import TWITCH_BOT_NAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL
from twitch.message_parser import parse_privmsg
from llm.ollama_worker import OllamaWorkerQueue

class IRCClient:
    def __init__(self):
        self.uri = "wss://irc-ws.chat.twitch.tv:443"
        self.buffer = []
        self.ollama_queue = OllamaWorkerQueue()
        asyncio.create_task(self.ollama_queue.start())

    async def connect(self):
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(f"PASS {TWITCH_OAUTH_TOKEN}")
            await websocket.send(f"NICK {TWITCH_BOT_NAME}")
            await websocket.send(f"JOIN #{TWITCH_CHANNEL}")
            print(f" Connected to #{TWITCH_CHANNEL} as {TWITCH_BOT_NAME}")

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
                    print("Disconnected. Reconnecting...")
                    break

    async def handle_message(self, message, websocket):
        msg_text = message["message"]

        if msg_text.startswith("{"):
            prompt = msg_text.lstrip("{").rstrip("}").strip()
            print(f"Prompt from chat: {prompt}")

            async def respond(reply):
                reply = reply.strip()
                max_len = 450  # Safe buffer
                if len(reply) > max_len:
                    reply = reply[:max_len - 3] + "..."  # Truncate with ellipsis

                print(f"📤 Sending reply to Twitch: {reply[:60]}...")
                await websocket.send(f"PRIVMSG #{TWITCH_CHANNEL} :{reply}")

            await self.ollama_queue.enqueue(prompt, respond)
