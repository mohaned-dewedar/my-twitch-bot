#!/usr/bin/env python3
"""
Leaderboard command functions with solid foundation.

These functions can be used standalone or integrated into chat commands.
All functions are designed with proper parameters and error handling.
"""

import asyncio
from typing import Optional, Union, List, Dict, Any
from db.database import Database
from db.channels import get_channel_id, add_channel
from db.users import get_or_create_user
from db.leaderboard import get_leaderboard, get_user_stats
from db.channel_users import get_channel_user_rank, get_top_streaks, get_channel_stats_summary


async def cmd_leaderboard(channel_identifier: Union[str, int], limit: int = 5) -> str:
    """
    Get leaderboard for a channel.
    
    Args:
        channel_identifier: Channel name (str) or channel_id (int)
        limit: Number of top users to show (default: 5)
        
    Returns:
        Formatted leaderboard string
    """
    try:
        # Resolve channel_id if needed
        if isinstance(channel_identifier, str):
            channel_id = await get_channel_id(channel_identifier)
            if channel_id is None:
                return f"❌ Channel '{channel_identifier}' not found in database"
            channel_name = channel_identifier
        else:
            channel_id = channel_identifier
            # Get channel name for display (simplified for now)
            channel_name = f"Channel {channel_id}"
        
        # Get leaderboard data
        leaderboard = await get_leaderboard(channel_id, limit=limit)
        
        if not leaderboard:
            return f"📭 No trivia data yet for #{channel_name}"
        
        # Format leaderboard
        lines = [f"🏆 TOP {len(leaderboard)} - #{channel_name}"]
        
        for i, user in enumerate(leaderboard, 1):
            username = user['twitch_username']
            correct = user['correct_answers']
            total = user['total_questions']
            accuracy = float(user['accuracy_pct'])
            
            # Format: "1. username: 15/20 (75.0%)"
            lines.append(f"{i}. {username}: {correct}/{total} ({accuracy}%)")
        
        return " | ".join(lines)
    
    except Exception as e:
        return f"❌ Error getting leaderboard: {str(e)}"


async def cmd_stats(username: str, channel_identifier: Union[str, int]) -> str:
    """
    Get personal statistics for a user in a channel.
    
    Args:
        username: Twitch username
        channel_identifier: Channel name (str) or channel_id (int)
        
    Returns:
        Formatted stats string
    """
    try:
        # Resolve channel_id if needed
        if isinstance(channel_identifier, str):
            channel_id = await get_channel_id(channel_identifier)
            if channel_id is None:
                return f"❌ Channel '{channel_identifier}' not found"
            channel_name = channel_identifier
        else:
            channel_id = channel_identifier
            channel_name = f"Channel {channel_id}"
        
        # Get user_id
        user_id = await get_or_create_user(username)
        
        # Get user stats
        stats = await get_user_stats(channel_id, user_id)
        
        if not stats or stats['total_questions'] == 0:
            return f"📊 {username} hasn't answered any questions in #{channel_name} yet"
        
        # Format stats
        correct = stats['correct_answers']
        total = stats['total_questions']
        accuracy = float(stats['accuracy_pct'])
        current_streak = stats['current_streak']
        best_streak = stats['best_streak']
        
        return (f"📊 {username} in #{channel_name}: "
                f"{correct}/{total} correct ({accuracy}%) | "
                f"Current streak: {current_streak} | "
                f"Best streak: {best_streak}")
    
    except Exception as e:
        return f"❌ Error getting stats: {str(e)}"


async def cmd_rank(username: str, channel_identifier: Union[str, int]) -> str:
    """
    Get user's current rank in channel leaderboard.
    
    Args:
        username: Twitch username
        channel_identifier: Channel name (str) or channel_id (int)
        
    Returns:
        Formatted rank string
    """
    try:
        # Resolve channel_id if needed
        if isinstance(channel_identifier, str):
            channel_id = await get_channel_id(channel_identifier)
            if channel_id is None:
                return f"❌ Channel '{channel_identifier}' not found"
            channel_name = channel_identifier
        else:
            channel_id = channel_identifier
            channel_name = f"Channel {channel_id}"
        
        # Get user_id
        user_id = await get_or_create_user(username)
        
        # Get user rank
        rank = await get_channel_user_rank(channel_id, user_id)
        
        if rank is None:
            return f"🔍 {username} is not ranked in #{channel_name} yet (no questions answered)"
        
        # Get user's current score for context
        stats = await get_user_stats(channel_id, user_id)
        correct = stats['correct_answers'] if stats else 0
        
        # Add ordinal suffix (1st, 2nd, 3rd, etc.)
        if rank == 1:
            rank_text = "1st 🥇"
        elif rank == 2:
            rank_text = "2nd 🥈"
        elif rank == 3:
            rank_text = "3rd 🥉"
        else:
            rank_text = f"{rank}th"
        
        return f"🏆 {username} is ranked {rank_text} in #{channel_name} with {correct} correct answers"
    
    except Exception as e:
        return f"❌ Error getting rank: {str(e)}"


async def cmd_streaks(channel_identifier: Union[str, int], limit: int = 5) -> str:
    """
    Get top streak holders for a channel.
    
    Args:
        channel_identifier: Channel name (str) or channel_id (int)
        limit: Number of top streaks to show (default: 5)
        
    Returns:
        Formatted streaks string
    """
    try:
        # Resolve channel_id if needed
        if isinstance(channel_identifier, str):
            channel_id = await get_channel_id(channel_identifier)
            if channel_id is None:
                return f"❌ Channel '{channel_identifier}' not found"
            channel_name = channel_identifier
        else:
            channel_id = channel_identifier
            channel_name = f"Channel {channel_id}"
        
        # Get top streaks
        streaks = await get_top_streaks(channel_id, limit=limit)
        
        if not streaks:
            return f"🔥 No streaks recorded yet in #{channel_name}"
        
        # Format streaks
        lines = [f"🔥 TOP STREAKS - #{channel_name}"]
        
        for i, user in enumerate(streaks, 1):
            username = user['twitch_username']
            best_streak = user['best_streak']
            current_streak = user['current_streak']
            
            # Show current streak if active
            streak_info = f"{best_streak}"
            if current_streak > 0:
                streak_info += f" (current: {current_streak})"
            
            lines.append(f"{i}. {username}: {streak_info}")
        
        return " | ".join(lines)
    
    except Exception as e:
        return f"❌ Error getting streaks: {str(e)}"


async def cmd_channel_summary(channel_identifier: Union[str, int]) -> str:
    """
    Get overall channel statistics summary.
    
    Args:
        channel_identifier: Channel name (str) or channel_id (int)
        
    Returns:
        Formatted summary string
    """
    try:
        # Resolve channel_id if needed
        if isinstance(channel_identifier, str):
            channel_id = await get_channel_id(channel_identifier)
            if channel_id is None:
                return f"❌ Channel '{channel_identifier}' not found"
            channel_name = channel_identifier
        else:
            channel_id = channel_identifier
            channel_name = f"Channel {channel_id}"
        
        # Get channel summary
        summary = await get_channel_stats_summary(channel_id)
        
        if not summary or summary['total_users'] == 0:
            return f"📈 No trivia activity yet in #{channel_name}"
        
        # Format summary
        total_users = summary['total_users']
        total_questions = summary['total_questions_answered']
        total_correct = summary['total_correct_answers']
        highest_streak = summary['highest_streak']
        avg_accuracy = float(summary['average_accuracy']) * 100
        
        return (f"📈 #{channel_name}: {total_users} users | "
                f"{total_correct}/{total_questions} correct ({avg_accuracy:.1f}%) | "
                f"Best streak: {highest_streak}")
    
    except Exception as e:
        return f"❌ Error getting summary: {str(e)}"


# Convenience functions for chat integration (simplified interfaces)
async def chat_leaderboard(channel_name: str) -> str:
    """Chat-friendly leaderboard (top 5)"""
    return await cmd_leaderboard(channel_name, limit=5)


async def chat_stats(username: str, channel_name: str) -> str:
    """Chat-friendly personal stats"""
    return await cmd_stats(username, channel_name)


async def chat_rank(username: str, channel_name: str) -> str:
    """Chat-friendly rank check"""
    return await cmd_rank(username, channel_name)


async def chat_streaks(channel_name: str) -> str:
    """Chat-friendly streak leaderboard"""
    return await cmd_streaks(channel_name, limit=5)