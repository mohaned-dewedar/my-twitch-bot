#!/usr/bin/env python3
"""
Quick script to display current leaderboard data
"""
import asyncio
from db.database import Database
from db.leaderboard import get_leaderboard
from db.channels import get_channel_id
from config import DATABASE_URL, TWITCH_CHANNEL

async def show_leaderboard():
    # Initialize database
    db = await Database.init(DATABASE_URL)
    
    # Get channel ID
    channel_id = await get_channel_id(TWITCH_CHANNEL)
    if not channel_id:
        print(f"❌ Channel {TWITCH_CHANNEL} not found in database")
        return
    
    print(f"🏆 LEADERBOARD for #{TWITCH_CHANNEL}")
    print("=" * 50)
    
    # Get top 10 users
    leaderboard = await get_leaderboard(channel_id, limit=10)
    
    if not leaderboard:
        print("📭 No trivia data yet - play some trivia to populate the leaderboard!")
        return
    
    print(f"{'Rank':<4} {'Username':<20} {'Correct':<7} {'Total':<7} {'Accuracy':<8} {'Best Streak':<6}")
    print("-" * 60)
    
    for i, user in enumerate(leaderboard, 1):
        username = user['twitch_username']
        correct = user['correct_answers']
        total = user['total_questions'] 
        accuracy = user['accuracy_pct']
        streak = user['best_streak']
        
        print(f"{i:<4} {username:<20} {correct:<7} {total:<7} {accuracy:<8}% {streak:<6}")

if __name__ == "__main__":
    asyncio.run(show_leaderboard())