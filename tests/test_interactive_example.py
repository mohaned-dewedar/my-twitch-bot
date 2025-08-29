#!/usr/bin/env python3
"""Simulate the interactive command that was failing"""

import asyncio
from db.database import Database
from config import DATABASE_URL
from leaderboard_commands import cmd_leaderboard

async def test_failing_case():
    db = await Database.init(DATABASE_URL)
    print("✅ Database initialized")
    
    # This was the failing case: leaderboard thecherryo 2
    result = await cmd_leaderboard("thecherryo", limit=2)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_failing_case())