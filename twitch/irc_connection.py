"""
Pure IRC connection handling for Twitch.

Manages WebSocket connection, IRC protocol messages (PING/PONG), 
and raw message processing without business logic.
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable
import websockets
from websockets import WebSocketClientProtocol
from dataclasses import dataclass


LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class IRCCredentials:
    """IRC connection credentials."""
    nick: str          # Bot username
    oauth: str         # OAuth token with oauth: prefix
    channel: str       # Channel to join (without #)


class IRCConnection:
    """
    Pure IRC protocol connection handler.
    
    Handles WebSocket connection to Twitch IRC, authentication,
    channel joining, PING/PONG responses, and message routing
    without any business logic.
    """
    
    def __init__(self, uri: str = "wss://irc-ws.chat.twitch.tv:443"):
        """
        Initialize IRC connection handler.
        
        Args:
            uri: Twitch IRC WebSocket URI
        """
        self.uri = uri
        self._ws: Optional[WebSocketClientProtocol] = None
        self._credentials: Optional[IRCCredentials] = None
        
        # Message handling callback
        self._message_handler: Optional[Callable[[str], Awaitable[None]]] = None
    
    def set_credentials(self, credentials: IRCCredentials) -> None:
        """
        Set IRC connection credentials.
        
        Args:
            credentials: IRC authentication and channel info
        """
        self._credentials = credentials
    
    def set_message_handler(self, handler: Callable[[str], Awaitable[None]]) -> None:
        """
        Set callback for handling received IRC messages.
        
        Args:
            handler: Async function to process IRC messages
        """
        self._message_handler = handler
    
    async def connect_and_authenticate(self) -> None:
        """
        Connect to IRC and authenticate.
        
        Raises:
            ValueError: If credentials not set
            ConnectionError: If connection fails
        """
        if not self._credentials:
            raise ValueError("IRC credentials not set")
            
        LOG.info(f"Connecting to Twitch IRC at {self.uri}")
        
        self._ws = await websockets.connect(self.uri)
        
        # Authenticate
        await self._ws.send(f"PASS {self._credentials.oauth}")
        await self._ws.send(f"NICK {self._credentials.nick}")
        await self._ws.send(f"JOIN #{self._credentials.channel}")
        
        LOG.info(f"Connected to #{self._credentials.channel} as {self._credentials.nick}")
    
    async def message_loop(self) -> None:
        """
        Main message processing loop.
        
        Handles incoming IRC messages, PING/PONG responses,
        and routes other messages to the configured handler.
        
        Raises:
            ConnectionError: If WebSocket is not connected
        """
        if not self._ws:
            raise ConnectionError("Not connected to IRC")
            
        async for raw_message in self._ws:
            message = raw_message.strip()
            LOG.debug(f"<< {message}")
            
            # Handle IRC protocol messages
            if message.startswith("PING"):
                pong_response = "PONG :tmi.twitch.tv"
                await self._ws.send(pong_response)
                LOG.debug(f">> {pong_response}")
                continue
            
            # Route other messages to handler
            if self._message_handler:
                try:
                    await self._message_handler(message)
                except Exception as e:
                    LOG.error(f"Error in message handler: {e}")
    
    async def send_raw_message(self, message: str) -> None:
        """
        Send a raw IRC message.
        
        Args:
            message: Raw IRC message to send
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._ws:
            raise ConnectionError("Not connected to IRC")
            
        await self._ws.send(message)
        LOG.debug(f">> {message[:80]}{'...' if len(message) > 80 else ''}")
    
    async def send_chat_message(self, text: str) -> None:
        """
        Send a chat message to the current channel.
        
        Args:
            text: Message text to send
            
        Raises:
            ConnectionError: If not connected
            ValueError: If credentials not set
        """
        if not self._credentials:
            raise ValueError("IRC credentials not set")
            
        privmsg = f"PRIVMSG #{self._credentials.channel} :{text}"
        await self.send_raw_message(privmsg)
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to IRC.
        
        Returns:
            True if WebSocket connection is active
        """
        return self._ws is not None and not self._ws.closed
    
    async def disconnect(self) -> None:
        """Close the IRC connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            LOG.info("Disconnected from IRC")
    
    def get_connection_info(self) -> dict:
        """
        Get current connection information.
        
        Returns:
            Dictionary with connection status and details
        """
        return {
            "connected": self.is_connected(),
            "uri": self.uri,
            "nick": self._credentials.nick if self._credentials else None,
            "channel": self._credentials.channel if self._credentials else None,
            "has_message_handler": self._message_handler is not None
        }