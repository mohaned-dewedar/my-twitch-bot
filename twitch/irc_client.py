import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional
import websockets
from websockets import WebSocketClientProtocol
from config import TWITCH_BOT_NAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL
from twitch.message_parser import parse_privmsg
from llm.ollama_worker import OllamaWorkerQueue
from data.data_loader import SmiteDataStore
from trivia.types import ApiTriviaHandler, SmiteTriviaHandler
from trivia.manager import TriviaManager


# --------------------------- Logging ---------------------------------

LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


# --------------------------- Settings --------------------------------

@dataclass(frozen=True)
class TwitchSettings:
    uri: str = "wss://irc-ws.chat.twitch.tv:443"
    nick: str = TWITCH_BOT_NAME
    oauth: str = TWITCH_OAUTH_TOKEN
    channel: str = TWITCH_CHANNEL
    # Rate limit: Twitch IRC recommends < 20 msgs / 30s for normal users
    max_msg_len: int = 450
    burst: int = 18
    window_seconds: int = 30


# --------------------------- Utilities --------------------------------

def clamp_chat(msg: str, max_len: int) -> str:
    return msg if len(msg) <= max_len else msg[: max_len - 3] + "..."


# --------------------------- IRC Client -------------------------------

class IRCClient:
    """
    Twitch IRC client with a minimal command router and trivia workflow.
    """
    def __init__(self, settings: TwitchSettings = TwitchSettings()) -> None:
        self.settings = settings
        self._ws: Optional[WebSocketClientProtocol] = None

        # External workers / data
        self.ollama_queue = OllamaWorkerQueue()
        self.api_handler = ApiTriviaHandler(use_custom=False)

        self.smite_store = SmiteDataStore()
        if not self.smite_store.load_data():
            LOG.warning("Failed to load Smite data.")
        else:
            LOG.info("Smite data loaded.")

        self.manager = TriviaManager()
        self.smite_handler = SmiteTriviaHandler(self.smite_store)

        # Trivia mode
        self.auto_trivia: bool = False
        self.auto_trivia_type: Optional[str] = None  # "api" | "smite" | None
        self._pending_auto_question: Optional[str] = None

        # Rate limiting
        self._sent_timestamps: list[float] = []

        # Command routing
        self._commands: Dict[str, Callable[[str, str], Optional[str]]] = {
            "!trivia-help": self._cmd_trivia_help,
            "!giveup": self._cmd_giveup,
            "!end trivia": self._cmd_end_trivia,
            "!answer": self._cmd_answer,
            "!trivia auto smite": self._cmd_trivia_auto_smite,
            "!trivia auto": self._cmd_trivia_auto,
            "!trivia smite": self._cmd_trivia_smite,
            "!trivia": self._cmd_trivia,
        }

    # ------------------------ Public API -----------------------------

    async def run(self) -> None:
        """
        Start background workers and maintain a persistent IRC connection with backoff.
        """
        asyncio.create_task(self.ollama_queue.start())

        backoff = 1
        while True:
            try:
                await self._connect_and_loop()
                backoff = 1
            except asyncio.CancelledError:
                raise
            except Exception as e:
                LOG.warning("Disconnected: %s. Reconnecting in %ss", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    # ------------------------ Core Loop ------------------------------

    async def _connect_and_loop(self) -> None:
        async with websockets.connect(self.settings.uri) as ws:
            self._ws = ws
            await ws.send(f"PASS {self.settings.oauth}")
            await ws.send(f"NICK {self.settings.nick}")
            await ws.send(f"JOIN #{self.settings.channel}")
            LOG.info("Connected to #%s as %s", self.settings.channel, self.settings.nick)

            async for raw in ws:
                msg = raw.strip()
                LOG.debug("<< %s", msg)

                if msg.startswith("PING"):
                    await ws.send("PONG :tmi.twitch.tv")
                    continue

                parsed = parse_privmsg(msg)
                if not parsed:
                    continue

                await self._handle_message(parsed["user"], parsed["message"])

    # ------------------------ Message Handling -----------------------

    async def _handle_message(self, username: str, message: str) -> None:
        response = self._dispatch_command(message, username)
        if response:
            await self._send(response)

        # If !giveup in auto mode, send next question separately
        if self._pending_auto_question:
            await asyncio.sleep(1)
            await self._send(self._pending_auto_question)
            self._pending_auto_question = None

        # In auto mode, if a correct answer just landed, queue the next question
        if self.auto_trivia and self.manager.should_ask_next():
            await asyncio.sleep(1)
            if self.auto_trivia_type == "smite":
                await self._send(self.manager.start_trivia(self.smite_handler, force=True))
            else:
                self.manager.start_trivia(self.api_handler, force=True)
                q = getattr(self.api_handler, "get_question", lambda: None)()
                if q and q.get("all_answers"):
                    await self._send(self._format_mcq(q))

    # ------------------------ Commands --------------------------------

    def _dispatch_command(self, message: str, username: str) -> Optional[str]:
        msg = message.strip()
        key = msg.lower()

        # Fast exact matches first
        if key in self._commands:
            return self._commands[key](message, username)

        # Prefix match for commands that take args (e.g., !answer ...)
        if key.startswith("!answer"):
            return self._commands["!answer"](message, username)

        return None
    def _current_mcq_answers(self) -> list[str]:
        """Return current MCQ answers if available, else []."""
        
        getq = getattr(self.api_handler, "get_question", None)
        if callable(getq):
            q = getq()
            if q and q.get("all_answers"):
                return list(q["all_answers"])
        return []

    def _cmd_trivia_help(self, _: str, __: str) -> str:
        return self.manager.get_help()

    def _cmd_giveup(self, _: str, __: str) -> str:
        answer = self.manager.end_trivia()
        if self.auto_trivia:
            if self.auto_trivia_type == "smite":
                self._pending_auto_question = self.manager.start_trivia(self.smite_handler, force=True)
            else:
                self.manager.start_trivia(self.api_handler, force=True)
                q = getattr(self.api_handler, "get_question", lambda: None)()
                self._pending_auto_question = self._format_mcq(q) if q and q.get("all_answers") else "Auto trivia continues!"
        else:
            self.auto_trivia = False
            self.auto_trivia_type = None
        return answer

    def _cmd_end_trivia(self, _: str, __: str) -> str:
        self.auto_trivia = False
        self.auto_trivia_type = None
        return "🛑 Auto trivia ended!"

    
    

    
    def _cmd_answer(self, message: str, username: str) -> str:
        raw = message[len("!answer"):].strip()
        guess = raw

        
        if len(raw) >= 1:
            letter = raw.split()[0].strip().lower()
            if len(letter) == 1 and "a" <= letter <= "z":
                answers = self._current_mcq_answers()
                idx = ord(letter) - ord("a")
                if 0 <= idx < len(answers):
                    guess = answers[idx]

        return self.manager.submit_answer(guess, username)


    def _cmd_trivia_auto_smite(self, _: str, __: str) -> str:
        self.auto_trivia, self.auto_trivia_type = True, "smite"
        return self.manager.start_trivia(self.smite_handler, force=True)

    def _cmd_trivia_auto(self, _: str, __: str) -> str:
        self.auto_trivia, self.auto_trivia_type = True, "api"
        self.manager.start_trivia(self.api_handler, force=True)
        q = getattr(self.api_handler, "get_question", lambda: None)()
        return self._format_mcq(q) if q and q.get("all_answers") else "Auto trivia started!"

    def _cmd_trivia_smite(self, _: str, __: str) -> str:
        self.auto_trivia = False
        self.auto_trivia_type = None
        return self.manager.start_trivia(self.smite_handler)

    def _cmd_trivia(self, _: str, __: str) -> str:
        self.auto_trivia = False
        self.auto_trivia_type = None
        result = self.manager.start_trivia(self.api_handler)
        q = getattr(self.api_handler, "get_question", lambda: None)()
        return self._format_mcq(q) if q and q.get("all_answers") else result

    # ------------------------ Formatting ------------------------------

    @staticmethod
    def _format_mcq(q: dict) -> str:
        answers = q.get("all_answers", [])
        opts = " ".join(f"{chr(0x1F1E6 + i)} {ans}" for i, ans in enumerate(answers))
        cat = q.get("category", "Unknown")
        return f"🎲 {q['question']} | {opts} | Category: {cat}"

    # ------------------------ Outbound IRC ----------------------------

    async def _send(self, message: str) -> None:
        if not self._ws:
            return
        # simple token-bucket window
        now = time.time()
        window_start = now - self.settings.window_seconds
        self._sent_timestamps = [t for t in self._sent_timestamps if t >= window_start]
        if len(self._sent_timestamps) >= self.settings.burst:
            sleep_for = self._sent_timestamps[0] + self.settings.window_seconds - now
            await asyncio.sleep(max(0.0, sleep_for))
        payload = f"PRIVMSG #{self.settings.channel} :{clamp_chat(message.strip(), self.settings.max_msg_len)}"
        LOG.debug(">> %s", payload[:80])
        await self._ws.send(payload)
        self._sent_timestamps.append(time.time())


# --------------------------- Entrypoint -------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(IRCClient().run())
    except KeyboardInterrupt:
        LOG.info("Shutting down…")