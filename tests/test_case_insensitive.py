#!/usr/bin/env python3
"""Test case-insensitive channel lookup"""

import asyncio
from db.database import Database
from config import DATABASE_URL
from leaderboard_commands import cmd_leaderboard

async def test_case_insensitive():
    db = await Database.init(DATABASE_URL)
    print("✅ Database initialized")
    
    # Test different case variations
    test_cases = [
        "thecherryo",           # all lowercase
        "TheCherryo",           # correct case
        "THECHERRYO",           # all uppercase
        "theCHERRYO",           # mixed case
        "tHeCheRrYo",           # random case
    ]
    
    print("🧪 Testing case-insensitive channel lookup:")
    print("-" * 50)
    
    for channel_name in test_cases:
        result = await cmd_leaderboard(channel_name, limit=1)
        print(f"Channel: '{channel_name}' -> {result}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_case_insensitive())