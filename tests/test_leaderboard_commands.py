#!/usr/bin/env python3
"""
Comprehensive test file for leaderboard commands.

Tests all command functions with various scenarios and edge cases.
"""

import asyncio
import sys
from db.database import Database
from config import DATABASE_URL, TWITCH_CHANNEL
from leaderboard_commands import (
    cmd_leaderboard, cmd_stats, cmd_rank, cmd_streaks, cmd_channel_summary,
    chat_leaderboard, chat_stats, chat_rank, chat_streaks
)


async def test_all_commands():
    """Test all leaderboard command functions"""
    
    print("🧪 TESTING LEADERBOARD COMMANDS")
    print("=" * 50)
    
    # Initialize database
    try:
        db = await Database.init(DATABASE_URL)
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test channel - using your configured channel
    test_channel = TWITCH_CHANNEL
    print(f"🎯 Using test channel: {test_channel}")
    print()
    
    # Test 1: Leaderboard
    print("1️⃣ TESTING LEADERBOARD")
    print("-" * 30)
    
    # Test with channel name
    result = await cmd_leaderboard(test_channel, limit=10)
    print(f"📊 Top 10 Leaderboard:\n{result}\n")
    
    # Test with smaller limit
    result = await cmd_leaderboard(test_channel, limit=3)
    print(f"📊 Top 3 Leaderboard:\n{result}\n")
    
    # Test with non-existent channel
    result = await cmd_leaderboard("nonexistent_channel")
    print(f"📊 Non-existent channel test:\n{result}\n")
    
    
    # Test 2: Stats
    print("2️⃣ TESTING PERSONAL STATS")
    print("-" * 30)
    
    # Test with existing user (your username from the leaderboard)
    result = await cmd_stats("thecherryo", test_channel)
    print(f"📈 Stats for thecherryo:\n{result}\n")
    
    # Test with non-existent user
    result = await cmd_stats("nonexistent_user", test_channel)
    print(f"📈 Stats for non-existent user:\n{result}\n")
    
    
    # Test 3: Rank
    print("3️⃣ TESTING RANK")
    print("-" * 30)
    
    # Test with existing user
    result = await cmd_rank("thecherryo", test_channel)
    print(f"🏆 Rank for thecherryo:\n{result}\n")
    
    # Test with non-existent user
    result = await cmd_rank("nonexistent_user", test_channel)
    print(f"🏆 Rank for non-existent user:\n{result}\n")
    
    
    # Test 4: Streaks
    print("4️⃣ TESTING STREAKS")
    print("-" * 30)
    
    # Test top streaks
    result = await cmd_streaks(test_channel, limit=5)
    print(f"🔥 Top 5 Streaks:\n{result}\n")
    
    # Test with non-existent channel
    result = await cmd_streaks("nonexistent_channel")
    print(f"🔥 Streaks for non-existent channel:\n{result}\n")
    
    
    # Test 5: Channel Summary
    print("5️⃣ TESTING CHANNEL SUMMARY")
    print("-" * 30)
    
    # Test channel summary
    result = await cmd_channel_summary(test_channel)
    print(f"📈 Channel Summary:\n{result}\n")
    
    
    # Test 6: Chat-friendly versions
    print("6️⃣ TESTING CHAT-FRIENDLY FUNCTIONS")
    print("-" * 30)
    
    result = await chat_leaderboard(test_channel)
    print(f"💬 Chat Leaderboard:\n{result}\n")
    
    result = await chat_stats("thecherryo", test_channel)
    print(f"💬 Chat Stats:\n{result}\n")
    
    result = await chat_rank("thecherryo", test_channel)
    print(f"💬 Chat Rank:\n{result}\n")
    
    result = await chat_streaks(test_channel)
    print(f"💬 Chat Streaks:\n{result}\n")
    
    
    # Test 7: Edge Cases
    print("7️⃣ TESTING EDGE CASES")
    print("-" * 30)
    
    # Test with channel_id instead of name
    try:
        # Get channel_id first
        from db.channels import get_channel_id
        channel_id = await get_channel_id(test_channel)
        if channel_id:
            result = await cmd_leaderboard(channel_id, limit=3)
            print(f"📊 Leaderboard by channel_id ({channel_id}):\n{result}\n")
        else:
            print("⚠️ Could not get channel_id for testing\n")
    except Exception as e:
        print(f"⚠️ Channel ID test failed: {e}\n")
    
    # Test with extreme limits
    result = await cmd_leaderboard(test_channel, limit=100)
    print(f"📊 Leaderboard with limit 100:\n{result}\n")
    
    result = await cmd_streaks(test_channel, limit=1)
    print(f"🔥 Top 1 Streak:\n{result}\n")
    
    print("✅ ALL TESTS COMPLETED!")


async def interactive_test():
    """Interactive test mode for manual testing"""
    
    print("🔧 INTERACTIVE TEST MODE")
    print("=" * 30)
    print("Available commands:")
    print("1. leaderboard <channel> [limit]")
    print("2. stats <username> <channel>")
    print("3. rank <username> <channel>")
    print("4. streaks <channel> [limit]")
    print("5. summary <channel>")
    print("6. quit")
    print()
    
    # Initialize database
    try:
        db = await Database.init(DATABASE_URL)
        print("✅ Database ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit" or command == "q":
                break
            
            parts = command.split()
            if not parts:
                continue
                
            cmd = parts[0]
            
            if cmd == "leaderboard":
                channel = parts[1] if len(parts) > 1 else TWITCH_CHANNEL
                limit = int(parts[2]) if len(parts) > 2 else 5
                result = await cmd_leaderboard(channel, limit)
                print(result)
                
            elif cmd == "stats":
                if len(parts) < 3:
                    print("Usage: stats <username> <channel>")
                    continue
                username, channel = parts[1], parts[2]
                result = await cmd_stats(username, channel)
                print(result)
                
            elif cmd == "rank":
                if len(parts) < 3:
                    print("Usage: rank <username> <channel>")
                    continue
                username, channel = parts[1], parts[2]
                result = await cmd_rank(username, channel)
                print(result)
                
            elif cmd == "streaks":
                channel = parts[1] if len(parts) > 1 else TWITCH_CHANNEL
                limit = int(parts[2]) if len(parts) > 2 else 5
                result = await cmd_streaks(channel, limit)
                print(result)
                
            elif cmd == "summary":
                channel = parts[1] if len(parts) > 1 else TWITCH_CHANNEL
                result = await cmd_channel_summary(channel)
                print(result)
                
            else:
                print(f"Unknown command: {cmd}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_all_commands())