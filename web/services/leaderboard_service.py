"""Service layer for leaderboard operations."""

import logging
from typing import List, Optional, Dict, Any
from web.models.leaderboard import UserStats, ChannelInfo, LeaderboardResponse, ChannelSummary
from web.models.channel import ChannelParams
from leaderboard_commands import cmd_leaderboard, cmd_channel_summary
from db.leaderboard import get_leaderboard
from db.channels import get_channel_id
from db.channel_users import get_channel_stats_summary

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Service for handling leaderboard business logic."""

    @staticmethod
    async def get_channel_leaderboard(channel_name: str, limit: int = 5) -> LeaderboardResponse:
        """
        Get formatted leaderboard for a channel.
        
        Args:
            channel_name: Channel name to get leaderboard for
            limit: Maximum number of entries to return
            
        Returns:
            LeaderboardResponse with formatted data
            
        Raises:
            ValueError: If channel not found or data invalid
        """
        try:
            # Validate channel exists and get ID
            channel_id = await get_channel_id(channel_name)
            if channel_id is None:
                raise ValueError(f"Channel '{channel_name}' not found")

            # Get raw leaderboard data
            raw_data = await get_leaderboard(channel_id, limit=limit)
            
            if not raw_data:
                # Return empty leaderboard for valid but inactive channels
                return LeaderboardResponse(
                    channel=ChannelInfo(
                        channel_name=channel_name,
                        channel_id=channel_id,
                        total_users=0,
                        total_questions=0
                    ),
                    users=[],
                    limit=limit
                )

            # Convert raw data to UserStats models
            user_stats = []
            for i, row in enumerate(raw_data, 1):
                user_stat = UserStats(
                    twitch_username=row['twitch_username'],
                    correct_answers=row['correct_answers'],
                    total_questions=row['total_questions'],
                    accuracy_pct=float(row['accuracy_pct']),
                    current_streak=row['current_streak'],
                    best_streak=row['best_streak'],
                    rank=i
                )
                user_stats.append(user_stat)

            # Calculate channel totals
            total_users = len(user_stats)
            total_questions = sum(user.total_questions for user in user_stats)

            return LeaderboardResponse(
                channel=ChannelInfo(
                    channel_name=channel_name,
                    channel_id=channel_id,
                    total_users=total_users,
                    total_questions=total_questions
                ),
                users=user_stats,
                limit=limit
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting leaderboard for {channel_name}: {e}")
            raise ValueError(f"Failed to retrieve leaderboard: {str(e)}")

    @staticmethod
    async def get_channel_summary(channel_name: str) -> ChannelSummary:
        """
        Get channel statistics summary.
        
        Args:
            channel_name: Channel name to get summary for
            
        Returns:
            ChannelSummary with aggregated stats
            
        Raises:
            ValueError: If channel not found or data invalid
        """
        try:
            # Validate channel exists and get ID
            channel_id = await get_channel_id(channel_name)
            if channel_id is None:
                raise ValueError(f"Channel '{channel_name}' not found")

            # Get raw summary data from database
            summary_data = await get_channel_stats_summary(channel_id)
            
            if not summary_data or summary_data['total_users'] == 0:
                # Return empty summary for valid but inactive channels
                return ChannelSummary(
                    channel_name=channel_name,
                    total_users=0,
                    total_questions_answered=0,
                    total_correct_answers=0,
                    average_accuracy=0.0,
                    highest_streak=0
                )

            # Map database results to ChannelSummary model
            return ChannelSummary(
                channel_name=channel_name,
                total_users=summary_data['total_users'],
                total_questions_answered=summary_data['total_questions_answered'],
                total_correct_answers=summary_data['total_correct_answers'],
                average_accuracy=float(summary_data['average_accuracy']) if summary_data['average_accuracy'] else 0.0,
                highest_streak=summary_data['highest_streak'] if summary_data['highest_streak'] else 0
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error getting summary for {channel_name}: {e}")
            raise ValueError(f"Failed to retrieve channel summary: {str(e)}")

    @staticmethod
    def validate_channel_params(params: ChannelParams) -> None:
        """
        Validate channel parameters.
        
        Args:
            params: Channel parameters to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not params.channel_name:
            raise ValueError("Channel name is required")
        
        if params.limit and (params.limit < 1 or params.limit > 50):
            raise ValueError("Limit must be between 1 and 50")