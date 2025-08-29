#!/usr/bin/env python3
"""
Direct database query to show all trivia statistics
"""
import asyncio
from db.database import Database
from config import DATABASE_URL

async def show_detailed_stats():
    db = await Database.init(DATABASE_URL)
    
    async with db.acquire() as conn:
        # Get all channel user stats
        result = await conn.fetch("""
            SELECT c.name as channel_name, u.twitch_username, 
                   cu.correct_answers, cu.total_questions, cu.current_streak, cu.best_streak,
                   cu.first_seen, cu.last_seen
            FROM channel_users cu
            JOIN users u ON cu.user_id = u.id 
            JOIN channels c ON cu.channel_id = c.id
            WHERE cu.total_questions > 0
            ORDER BY cu.correct_answers DESC
        """)
        
        if not result:
            print("No trivia data found!")
            return
            
        print("🎯 DETAILED TRIVIA STATISTICS")
        print("=" * 80)
        
        for row in result:
            print(f"Channel: {row['channel_name']}")
            print(f"User: {row['twitch_username']}")
            print(f"Score: {row['correct_answers']}/{row['total_questions']} correct")
            print(f"Accuracy: {row['correct_answers']/row['total_questions']*100:.1f}%")
            print(f"Current Streak: {row['current_streak']}")
            print(f"Best Streak: {row['best_streak']}")
            print(f"First Seen: {row['first_seen']}")
            print(f"Last Seen: {row['last_seen']}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(show_detailed_stats())