"""Pydantic models for channel-related data."""

from typing import Optional
from pydantic import BaseModel, Field, validator
import re


class ChannelParams(BaseModel):
    """Channel request parameters."""
    channel_name: str = Field(..., min_length=1, max_length=50, description="Twitch channel name")
    limit: Optional[int] = Field(5, ge=1, le=50, description="Number of leaderboard entries")
    
    @validator('channel_name')
    def validate_channel_name(cls, v):
        """Validate channel name format (basic Twitch username rules)."""
        if not re.match(r'^[a-zA-Z0-9_]{1,25}$', v):
            raise ValueError('Channel name must contain only letters, numbers, and underscores')
        return v.lower()


class OverlayConfig(BaseModel):
    """Configuration for overlay display."""
    theme: str = Field("default", description="Overlay theme")
    compact_mode: bool = Field(False, description="Use compact display mode")
    show_accuracy: bool = Field(True, description="Show accuracy percentages")
    show_streaks: bool = Field(True, description="Show streak information")
    refresh_interval: int = Field(15, ge=5, le=300, description="Auto-refresh interval in seconds")
    max_entries: int = Field(5, ge=1, le=20, description="Maximum leaderboard entries to display")