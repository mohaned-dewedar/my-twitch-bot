"""
Refactored Twitch IRC client using focused, single-responsibility classes.

This is a clean rewrite of the IRC client that delegates responsibilities
to specialized components for better maintainability and testing.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

# Configuration and utilities
from config import TWITCH_BOT_NAME, TWITCH_OAUTH_TOKEN, TWITCH_CHANNEL
from twitch.message_parser import parse_privmsg

# Refactored components
from twitch.irc_connection import IRCConnection, IRCCredentials
from twitch.rate_limiter import RateLimiter, RateLimitSettings
from twitch.command_router import CommandRouter
from twitch.trivia_orchestrator import TriviaOrchestrator
from twitch.chat_api_client import ChatAPIClient
from twitch.message_utils import is_valid_twitch_message

# Business logic
from db.trivia_handlers import GeneralTriviaHandler, SmiteTriviaHandler
from trivia.manager import TriviaManager

# Database integration
from db.users import get_or_create_user
from db.channels import get_channel_id, add_channel
from db.sessions import start_session, get_active_session

# Leaderboard commands
from leaderboard_commands import (
    cmd_leaderboard, cmd_stats, cmd_rank, cmd_streaks, cmd_channel_summary
)


LOG = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


@dataclass(frozen=True)
class TwitchSettings:
    """Consolidated settings for Twitch IRC client."""
    uri: str = "wss://irc-ws.chat.twitch.tv:443"
    nick: str = TWITCH_BOT_NAME
    oauth: str = TWITCH_OAUTH_TOKEN
    channel: str = TWITCH_CHANNEL
    chat_api_url: str = "http://localhost:8000/chat"


class IRCClient:
    """
    Refactored Twitch IRC client with focused responsibilities.
    
    This client coordinates between specialized components:
    - IRCConnection: Pure IRC protocol handling
    - RateLimiter: Message rate limiting
    - CommandRouter: Command dispatch
    - TriviaOrchestrator: Auto trivia flow management
    - ChatAPIClient: External API integration
    - TriviaManager: Trivia session state
    """
    
    def __init__(self, settings: TwitchSettings = TwitchSettings()) -> None:
        """
        Initialize IRC client with specialized components.
        
        Args:
            settings: Configuration for Twitch connection
        """
        self.settings = settings
        
        # Initialize specialized components
        self._setup_components()
        
        # Initialize business logic components
        self.manager = TriviaManager()
        self.general_handler: Optional[GeneralTriviaHandler] = None
        self.smite_handler: Optional[SmiteTriviaHandler] = None
        
        # Database state
        self.channel_id: Optional[int] = None
        self.current_session_id: Optional[int] = None
    
    def _setup_components(self) -> None:
        """Initialize and configure all specialized components."""
        # IRC connection
        self.connection = IRCConnection(self.settings.uri)
        credentials = IRCCredentials(
            nick=self.settings.nick,
            oauth=self.settings.oauth,
            channel=self.settings.channel
        )
        self.connection.set_credentials(credentials)
        self.connection.set_message_handler(self._handle_irc_message)
        
        # Rate limiting
        rate_settings = RateLimitSettings(burst=18, window_seconds=30, max_msg_len=450)
        self.rate_limiter = RateLimiter(rate_settings)
        
        # Command routing
        self.command_router = CommandRouter()
        
        # Trivia orchestration
        self.trivia_orchestrator = TriviaOrchestrator()
        self.trivia_orchestrator.set_message_sender(self._send_message)
        
        # External API client
        self.chat_api = ChatAPIClient(self.settings.chat_api_url)
        self.chat_api.set_message_sender(self._send_message)
        
        # Register commands after all components are created
        self._register_commands()
    
    def _register_commands(self) -> None:
        """Register all chat commands with their handlers."""
        # Exact command matches
        exact_commands = {
            "!trivia-help": self._cmd_trivia_help,
            "!giveup": self._cmd_giveup,
            "!end trivia": self._cmd_end_trivia,
            "!trivia auto smite": self._cmd_trivia_auto_smite,
            "!trivia auto": self._cmd_trivia_auto,
            "!trivia smite": self._cmd_trivia_smite,
            "!trivia": self._cmd_trivia,
            # Leaderboard commands
            "!leaderboard": self._cmd_leaderboard,
            "!top": self._cmd_leaderboard,  # Alternative alias
            "!streaks": self._cmd_streaks,
            "!summary": self._cmd_summary,
        }
        self.command_router.register_commands_batch(exact_commands)
        
        # Prefix commands (take arguments)
        self.command_router.register_prefix_command("!answer", self._cmd_answer)
        self.command_router.register_prefix_command("!ask", self.chat_api.handle_ask_command)
        self.command_router.register_prefix_command("!chat", self.chat_api.handle_chat_command)
        # Leaderboard prefix commands (support optional usernames)
        self.command_router.register_prefix_command("!stats", self._cmd_stats)
        self.command_router.register_prefix_command("!rank", self._cmd_rank)
    
    async def run(self) -> None:
        """
        Start the IRC client with automatic reconnection.
        
        Initializes database handlers and maintains persistent connection
        with exponential backoff on failures.
        """
        LOG.info("Starting CherryBott IRC client...")
        
        # Initialize database handlers
        await self._init_database_handlers()
        
        # Connection loop with backoff
        backoff = 1
        while True:
            try:
                await self._connect_and_run()
                backoff = 1  # Reset on successful connection
            except asyncio.CancelledError:
                LOG.info("Client shutdown requested")
                break
            except Exception as e:
                LOG.warning(f"Connection failed: {e}. Reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)  # Max 30s backoff
    
    async def _connect_and_run(self) -> None:
        """Connect to IRC and run the message loop."""
        await self.connection.connect_and_authenticate()
        await self.connection.message_loop()
    
    async def _init_database_handlers(self) -> None:
        """Initialize database trivia handlers and channel registration."""
        try:
            from config import DATABASE_URL
            from db.database import Database
            
            # Initialize database connection
            db = await Database.init(DATABASE_URL)
            
            # Register/get channel in database
            await self._init_database_channel()
            
            # Create handlers
            self.general_handler = GeneralTriviaHandler(db)
            self.smite_handler = SmiteTriviaHandler(db)
            
            # Configure trivia orchestrator
            self.trivia_orchestrator.set_handlers(self.general_handler, self.smite_handler)
            
            LOG.info("Database trivia handlers initialized successfully")
        except Exception as e:
            LOG.error(f"Failed to initialize database handlers: {e}")
            # Handlers remain None - commands will show error messages
    
    async def _init_database_channel(self) -> None:
        """Register the channel in the database and get channel_id."""
        try:
            # Try to get existing channel
            self.channel_id = await get_channel_id(self.settings.channel)
            
            if self.channel_id is None:
                # Create new channel record
                await add_channel(
                    twitch_channel_id=self.settings.channel,
                    name=self.settings.channel
                )
                self.channel_id = await get_channel_id(self.settings.channel)
                LOG.info(f"Created new channel record: {self.settings.channel} -> {self.channel_id}")
            else:
                LOG.info(f"Using existing channel: {self.settings.channel} -> {self.channel_id}")
                
        except Exception as e:
            LOG.error(f"Failed to initialize channel in database: {e}")
            self.channel_id = None
    
    async def _handle_irc_message(self, raw_message: str) -> None:
        """
        Handle incoming IRC message.
        
        Args:
            raw_message: Raw IRC message from WebSocket
        """
        # Parse IRC message
        parsed = parse_privmsg(raw_message)
        if not parsed:
            return
        
        username = parsed["user"]
        message = parsed["message"]
        
        # Route to command handler
        response = await self.command_router.dispatch_command(message, username)
        if response:
            await self._send_message(response)
        
        # Handle async trivia operations
        await self._handle_trivia_flow()
    
    async def _handle_trivia_flow(self) -> None:
        """Handle complex trivia flow operations."""
        # Process pending async questions
        await self.trivia_orchestrator.handle_pending_questions(self.manager)
        
        # Handle auto-trivia progression
        await self.trivia_orchestrator.handle_auto_progression(self.manager)
    
    async def _send_message(self, message: str) -> None:
        """
        Send a message to chat with rate limiting.
        
        Args:
            message: Message text to send
        """
        if not is_valid_twitch_message(message):
            LOG.warning(f"Invalid message rejected: {repr(message)}")
            return
        
        # Apply rate limiting
        await self.rate_limiter.wait_if_needed()
        
        # Clamp message length and send
        clamped_message = self.rate_limiter.clamp_message_length(message)
        await self.connection.send_chat_message(clamped_message)
        
        # Record for rate limiting
        self.rate_limiter.record_message_sent()
    
    # ======================== COMMAND HANDLERS ========================
    
    def _cmd_trivia_help(self, _: str, __: str) -> str:
        """Handle !trivia-help command."""
        return self.manager.get_help()
    
    def _cmd_giveup(self, _: str, __: str) -> str:
        """Handle !giveup command."""
        return self.trivia_orchestrator.handle_giveup(self.manager)
    
    def _cmd_end_trivia(self, _: str, __: str) -> str:
        """Handle !end trivia command."""
        return self.trivia_orchestrator.end_trivia_mode()
    
    async def _cmd_answer(self, message: str, username: str) -> str:
        """Handle !answer command with MCQ shortcuts."""
        raw_answer = message[len("!answer"):].strip()
        
        # Handle letter shortcuts for MCQ
        if len(raw_answer) >= 1:
            first_word = raw_answer.split()[0].strip().lower()
            if len(first_word) == 1 and "a" <= first_word <= "z":
                # Try to convert letter to MCQ option
                if self.manager.active_handler:
                    question = self.manager.active_handler.get_question()
                    if question and question.get("answer_options"):
                        options = question["answer_options"]
                        letter_index = ord(first_word) - ord("a")
                        if 0 <= letter_index < len(options):
                            raw_answer = options[letter_index]
        
        # Get database context for tracking
        user_id = None
        session_id = self.current_session_id
        
        if self.channel_id is not None:
            try:
                user_id = await get_or_create_user(username)
                # Create session if none exists
                if session_id is None:
                    session_id = await start_session(self.channel_id, user_id)
                    self.current_session_id = session_id
                    LOG.info(f"Started new trivia session: {session_id}")
            except Exception as e:
                LOG.error(f"Failed to get user/session info: {e}")
        
        return await self.manager.submit_answer(
            raw_answer, username, user_id, self.channel_id, session_id
        )
    
    def _cmd_trivia_auto_smite(self, _: str, __: str) -> str:
        """Handle !trivia auto smite command."""
        return self.trivia_orchestrator.start_auto_trivia("smite")
    
    def _cmd_trivia_auto(self, _: str, __: str) -> str:
        """Handle !trivia auto command."""
        return self.trivia_orchestrator.start_auto_trivia("general")
    
    def _cmd_trivia_smite(self, _: str, __: str) -> str:
        """Handle !trivia smite command."""
        return self.trivia_orchestrator.start_single_trivia("smite")
    
    def _cmd_trivia(self, _: str, __: str) -> str:
        """Handle !trivia command."""
        return self.trivia_orchestrator.start_single_trivia("general")
    
    # ======================== LEADERBOARD COMMANDS ========================
    
    async def _cmd_leaderboard(self, _: str, __: str) -> str:
        """Handle !leaderboard command."""
        try:
            return await cmd_leaderboard(self.settings.channel, limit=5)
        except Exception as e:
            return f"❌ Error getting leaderboard: {str(e)}"
    
    async def _cmd_stats(self, message: str, username: str) -> str:
        """Handle !stats command with optional username."""
        try:
            # Check if a specific username was provided
            parts = message.split()
            if len(parts) > 1:
                target_username = parts[1].strip()
            else:
                target_username = username  # Default to the person asking
            
            return await cmd_stats(target_username, self.settings.channel)
        except Exception as e:
            return f"❌ Error getting stats: {str(e)}"
    
    async def _cmd_rank(self, message: str, username: str) -> str:
        """Handle !rank command with optional username."""
        try:
            # Check if a specific username was provided
            parts = message.split()
            if len(parts) > 1:
                target_username = parts[1].strip()
            else:
                target_username = username  # Default to the person asking
            
            return await cmd_rank(target_username, self.settings.channel)
        except Exception as e:
            return f"❌ Error getting rank: {str(e)}"
    
    async def _cmd_streaks(self, _: str, __: str) -> str:
        """Handle !streaks command."""
        try:
            return await cmd_streaks(self.settings.channel, limit=5)
        except Exception as e:
            return f"❌ Error getting streaks: {str(e)}"
    
    async def _cmd_summary(self, _: str, __: str) -> str:
        """Handle !summary command."""
        try:
            return await cmd_channel_summary(self.settings.channel)
        except Exception as e:
            return f"❌ Error getting summary: {str(e)}"
    
    # ======================== STATUS & DEBUGGING ========================
    
    def get_status(self) -> dict:
        """Get comprehensive client status."""
        return {
            "connection": self.connection.get_connection_info(),
            "rate_limiter": self.rate_limiter.get_current_usage(),
            "trivia_orchestrator": self.trivia_orchestrator.get_status(),
            "chat_api": self.chat_api.get_status(),
            "commands": self.command_router.get_registered_commands(),
            "trivia_manager": self.manager.get_status() if hasattr(self.manager, 'get_status') else "active"
        }


# ======================== ENTRY POINT ========================

if __name__ == "__main__":
    try:
        asyncio.run(IRCClient().run())
    except KeyboardInterrupt:
        LOG.info("Shutting down...")
    except Exception as e:
        LOG.error(f"Fatal error: {e}")
        raise