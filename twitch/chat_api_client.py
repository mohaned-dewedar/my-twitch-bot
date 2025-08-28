"""
External chat API client for handling AI-powered responses.

Manages HTTP requests to external chat APIs and provides clean integration
with the IRC client for !ask and !chat commands.
"""

import asyncio
import logging
import aiohttp
from typing import Optional, Callable, Awaitable
from .message_utils import strip_markdown


LOG = logging.getLogger(__name__)


class ChatAPIClient:
    """
    Client for external chat API integration.
    
    Handles async HTTP requests to chat APIs and manages response processing
    including markdown stripping for Twitch compatibility.
    """
    
    def __init__(self, api_url: str = "http://localhost:8000/chat", timeout: int = 10):
        """
        Initialize chat API client.
        
        Args:
            api_url: URL of the external chat API endpoint
            timeout: Request timeout in seconds
        """
        self.api_url = api_url
        self.timeout = timeout
        self._send_message: Optional[Callable[[str], Awaitable[None]]] = None
    
    def set_message_sender(self, sender: Callable[[str], Awaitable[None]]) -> None:
        """
        Set the message sending callback.
        
        Args:
            sender: Async function to send messages to chat
        """
        self._send_message = sender
    
    def handle_ask_command(self, message: str, username: str) -> Optional[str]:
        """
        Handle !ask command by queuing async API request.
        
        Args:
            message: Full message including "!ask " prefix
            username: Username who sent the command
            
        Returns:
            None (response sent async) or error message
        """
        # Extract the question from the message
        question = message[4:].strip() if len(message) > 4 else ""
        if not question:
            return "❌ Please provide a question after !ask"
        
        # Queue the async chat API call
        asyncio.create_task(self._handle_chat_request(question, username))
        return None  # Don't send immediate response, wait for async result
    
    def handle_chat_command(self, message: str, username: str) -> Optional[str]:
        """
        Handle !chat command by queuing async API request.
        
        Args:
            message: Full message including "!chat " prefix
            username: Username who sent the command
            
        Returns:
            None (response sent async) or error message
        """
        # Extract the question from the message
        question = message[6:].strip() if len(message) > 6 else ""
        if not question:
            return "❌ Please provide a question after !chat"
        
        # Queue the async chat API call
        asyncio.create_task(self._handle_chat_request(question, username))
        return None  # Don't send immediate response, wait for async result
    
    async def _handle_chat_request(self, question: str, username: str) -> None:
        """
        Handle async chat API request and send response to chat.
        
        Args:
            question: User's question to send to API
            username: Username who asked the question
        """
        if not self._send_message:
            LOG.error("No message sender configured for ChatAPIClient")
            return
            
        try:
            response_text = await self._make_api_request(question)
            if response_text:
                # Strip markdown formatting for Twitch chat compatibility
                clean_response = strip_markdown(response_text)
                await self._send_message(f"@{username} {clean_response}")
            else:
                await self._send_message(f"@{username} ❌ No response received from API")
                
        except aiohttp.ClientError as e:
            LOG.error(f"Chat API request failed: {e}")
            await self._send_message(f"@{username} ❌ Failed to connect to chat API")
        except Exception as e:
            LOG.error(f"Unexpected error in chat request: {e}")
            await self._send_message(f"@{username} ❌ An error occurred")
    
    async def _make_api_request(self, question: str) -> Optional[str]:
        """
        Make HTTP request to chat API.
        
        Args:
            question: Question to send to the API
            
        Returns:
            Response text from API or None if failed
        """
        payload = {
            "message": question,
            "search_mode": "hybrid",
            "n_results": 3
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "No response received")
                    else:
                        LOG.warning(f"API returned status {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            LOG.error(f"API request timed out after {self.timeout}s")
            return None
        except aiohttp.ClientError as e:
            LOG.error(f"API request failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if the chat API is available.
        
        Returns:
            True if API responds, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url.replace('/chat', '/health'),
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            LOG.debug(f"API health check failed: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        Get client status information.
        
        Returns:
            Dictionary with client configuration and state
        """
        return {
            "api_url": self.api_url,
            "timeout": self.timeout,
            "has_message_sender": self._send_message is not None
        }