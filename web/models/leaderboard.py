"""Pydantic models for leaderboard API responses."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class UserStats(BaseModel):
    """Individual user statistics."""
    twitch_username: str = Field(..., description="Twitch username")
    correct_answers: int = Field(..., ge=0, description="Number of correct answers")
    total_questions: int = Field(..., ge=0, description="Total questions answered")
    accuracy_pct: float = Field(..., ge=0, le=100, description="Accuracy percentage")
    current_streak: int = Field(..., ge=0, description="Current correct answer streak")
    best_streak: int = Field(..., ge=0, description="Best streak achieved")
    rank: Optional[int] = Field(None, ge=1, description="Current rank in channel")


class ChannelInfo(BaseModel):
    """Channel information."""
    channel_name: str = Field(..., description="Channel name")
    channel_id: int = Field(..., ge=1, description="Channel database ID")
    total_users: int = Field(..., ge=0, description="Total users with stats")
    total_questions: int = Field(..., ge=0, description="Total questions answered")


class LeaderboardResponse(BaseModel):
    """Complete leaderboard response."""
    channel: ChannelInfo
    users: List[UserStats] = Field(..., description="Leaderboard entries")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    limit: int = Field(..., ge=1, le=50, description="Number of entries returned")


class ChannelSummary(BaseModel):
    """Channel statistics summary."""
    channel_name: str = Field(..., description="Channel name")
    total_users: int = Field(..., ge=0, description="Total active users")
    total_questions_answered: int = Field(..., ge=0, description="Total questions answered")
    total_correct_answers: int = Field(..., ge=0, description="Total correct answers")
    average_accuracy: float = Field(..., ge=0, le=1, description="Average accuracy (0-1)")
    highest_streak: int = Field(..., ge=0, description="Highest streak in channel")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Data timestamp")


class ErrorResponse(BaseModel):
    """API error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")