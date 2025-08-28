"""
Rate limiting functionality for Twitch IRC client.

Implements a token bucket algorithm to respect Twitch's rate limits:
- Maximum 18 messages per 30-second sliding window for normal users
- Automatic delays when rate limit is reached
"""

import asyncio
import time
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class RateLimitSettings:
    """Configuration for rate limiting behavior."""
    burst: int = 18              # Maximum messages in window
    window_seconds: int = 30     # Time window in seconds
    max_msg_len: int = 450      # Maximum message length for Twitch


class RateLimiter:
    """
    Token bucket rate limiter for Twitch IRC messages.
    
    Prevents exceeding Twitch's rate limits by tracking message timestamps
    and automatically delaying sends when necessary.
    """
    
    def __init__(self, settings: RateLimitSettings = RateLimitSettings()):
        """
        Initialize rate limiter with configuration.
        
        Args:
            settings: Rate limiting configuration parameters
        """
        self.settings = settings
        self._sent_timestamps: List[float] = []
        
    async def wait_if_needed(self) -> None:
        """
        Check rate limits and sleep if necessary before sending.
        
        This method should be called before each message send to ensure
        compliance with Twitch's rate limiting requirements.
        """
        now = time.time()
        window_start = now - self.settings.window_seconds
        
        # Remove timestamps outside the current window
        self._sent_timestamps = [
            timestamp for timestamp in self._sent_timestamps 
            if timestamp >= window_start
        ]
        
        # Check if we're at the rate limit
        if len(self._sent_timestamps) >= self.settings.burst:
            # Calculate how long to wait until oldest message expires
            oldest_timestamp = self._sent_timestamps[0]
            sleep_time = oldest_timestamp + self.settings.window_seconds - now
            
            if sleep_time > 0:
                print(f"[RATE LIMIT] Waiting {sleep_time:.1f}s before sending message")
                await asyncio.sleep(sleep_time)
    
    def record_message_sent(self) -> None:
        """
        Record that a message was sent at the current time.
        
        Call this immediately after successfully sending a message
        to maintain accurate rate limiting state.
        """
        self._sent_timestamps.append(time.time())
        
    def clamp_message_length(self, message: str) -> str:
        """
        Truncate message to fit within Twitch's length limits.
        
        Args:
            message: Original message text
            
        Returns:
            Message truncated to max length with ellipsis if needed
        """
        if len(message) <= self.settings.max_msg_len:
            return message
        return message[: self.settings.max_msg_len - 3] + "..."
    
    def get_current_usage(self) -> dict:
        """
        Get current rate limiting statistics.
        
        Returns:
            Dictionary with current message count, limit, and window info
        """
        now = time.time()
        window_start = now - self.settings.window_seconds
        
        # Clean old timestamps
        active_timestamps = [
            timestamp for timestamp in self._sent_timestamps 
            if timestamp >= window_start
        ]
        
        return {
            "messages_in_window": len(active_timestamps),
            "max_messages": self.settings.burst,
            "window_seconds": self.settings.window_seconds,
            "time_until_reset": (
                self.settings.window_seconds - (now - active_timestamps[0])
                if active_timestamps else 0
            )
        }
        
    def is_at_limit(self) -> bool:
        """
        Check if we're currently at the rate limit.
        
        Returns:
            True if at or above rate limit, False otherwise
        """
        now = time.time()
        window_start = now - self.settings.window_seconds
        
        active_count = sum(
            1 for timestamp in self._sent_timestamps 
            if timestamp >= window_start
        )
        
        return active_count >= self.settings.burst