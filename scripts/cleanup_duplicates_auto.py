#!/usr/bin/env python3
"""
Automatic database cleanup script to remove duplicate question banks and questions.
Keeps the most recent version of each unique question bank.
"""

import asyncio
from typing import Dict, List, Tuple
from db.database import Database
from config import DATABASE_URL


async def cleanup_database():
    """Main function to clean up database duplicates"""
    print("🧹 CherryBott Database Cleanup (AUTOMATIC)")
    print("=" * 50)
    
    # Initialize database connection
    db = await Database.init(DATABASE_URL)
    
    try:
        # Show current state
        await show_current_state(db)
        
        print("\n🧹 Starting automatic cleanup process...")
        
        # Identify and remove duplicates
        duplicates_removed = await remove_duplicate_question_banks(db)
        
        # Remove empty question banks
        empty_removed = await remove_empty_question_banks(db)
        
        # Verify cleanup
        await verify_cleanup(db)
        
        # Show final results
        print(f"\n✅ Cleanup completed successfully!")
        print(f"   📦 Removed {duplicates_removed} duplicate question banks")
        print(f"   🗑️  Removed {empty_removed} empty question banks")
        
        # Show final state
        print("\n" + "="*50)
        print("📊 FINAL DATABASE STATE:")
        await show_current_state(db)
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise
    finally:
        await Database.close()


async def show_current_state(db):
    """Display current database state"""
    async with db.acquire() as conn:
        # Count question banks
        bank_count = await conn.fetchval("SELECT COUNT(*) FROM question_banks")
        
        # Count total questions  
        question_count = await conn.fetchval("SELECT COUNT(*) FROM questions")
        
        # Count by source type
        source_counts = await conn.fetch("""
            SELECT qb.source_type, COUNT(q.id) as question_count, COUNT(qb.id) as bank_count
            FROM question_banks qb
            LEFT JOIN questions q ON qb.id = q.bank_id
            GROUP BY qb.source_type
            ORDER BY qb.source_type
        """)
        
        print(f"   📦 Question Banks: {bank_count}")
        print(f"   📋 Total Questions: {question_count}")
        
        for source in source_counts:
            print(f"   • {source['source_type']}: {source['bank_count']} banks, {source['question_count']} questions")


async def remove_duplicate_question_banks(db) -> int:
    """
    Remove duplicate question banks, keeping only the most recent one of each type.
    Returns the number of banks removed.
    """
    print("\n🔍 Identifying duplicate question banks...")
    
    async with db.acquire() as conn:
        # Find duplicate banks - same name and source_type
        duplicates = await conn.fetch("""
            SELECT name, source_type, description, COUNT(*) as duplicate_count,
                   array_agg(id ORDER BY created_at DESC) as bank_ids,
                   array_agg(created_at ORDER BY created_at DESC) as created_dates
            FROM question_banks
            GROUP BY name, source_type, description
            HAVING COUNT(*) > 1
        """)
        
        if not duplicates:
            print("   ✅ No duplicate question banks found.")
            return 0
            
        total_removed = 0
        
        for dup in duplicates:
            bank_ids = dup['bank_ids']
            keep_id = bank_ids[0]  # Most recent (first in DESC order)
            remove_ids = bank_ids[1:]  # Older duplicates
            
            print(f"\n   🔄 Processing: {dup['name'][:50]}{'...' if len(dup['name']) > 50 else ''}")
            print(f"      📅 Found {dup['duplicate_count']} copies")
            print(f"      ✅ Keeping bank ID {keep_id} (most recent)")
            print(f"      🗑️  Removing {len(remove_ids)} older copies")
            
            # Delete the older duplicate banks (CASCADE will remove associated questions)
            for remove_id in remove_ids:
                question_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM questions WHERE bank_id = $1", remove_id
                )
                
                await conn.execute(
                    "DELETE FROM question_banks WHERE id = $1", remove_id
                )
                
                print(f"         💣 Deleted bank {remove_id} ({question_count} questions)")
                total_removed += 1
                
        return total_removed


async def remove_empty_question_banks(db) -> int:
    """
    Remove question banks that have no associated questions.
    Returns the number of empty banks removed.
    """
    print(f"\n🔍 Identifying empty question banks...")
    
    async with db.acquire() as conn:
        # Find banks with no questions
        empty_banks = await conn.fetch("""
            SELECT qb.id, qb.name, qb.source_type
            FROM question_banks qb
            LEFT JOIN questions q ON qb.id = q.bank_id
            WHERE q.id IS NULL
        """)
        
        if not empty_banks:
            print("   ✅ No empty question banks found.")
            return 0
            
        print(f"   🗑️  Found {len(empty_banks)} empty question banks")
        
        # Remove empty banks
        removed_count = 0
        for bank in empty_banks:
            await conn.execute("DELETE FROM question_banks WHERE id = $1", bank['id'])
            removed_count += 1
            print(f"      💣 Deleted: {bank['name'][:40]}{'...' if len(bank['name']) > 40 else ''} (ID {bank['id']})")
            
        return removed_count


async def verify_cleanup(db):
    """Verify that cleanup was successful"""
    print(f"\n🔍 Verifying cleanup results...")
    
    async with db.acquire() as conn:
        # Check for remaining duplicates
        remaining_dups = await conn.fetchval("""
            SELECT COUNT(*)
            FROM (
                SELECT name, source_type, description, COUNT(*) as dup_count
                FROM question_banks
                GROUP BY name, source_type, description
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        
        # Check for empty banks
        empty_banks = await conn.fetchval("""
            SELECT COUNT(*)
            FROM question_banks qb
            LEFT JOIN questions q ON qb.id = q.bank_id
            WHERE q.id IS NULL
        """)
        
        if remaining_dups == 0 and empty_banks == 0:
            print("   ✅ Verification successful - database is clean!")
        else:
            print(f"   ⚠️  Verification issues:")
            if remaining_dups > 0:
                print(f"      • {remaining_dups} duplicate bank groups still exist")
            if empty_banks > 0:
                print(f"      • {empty_banks} empty banks still exist")


if __name__ == "__main__":
    try:
        asyncio.run(cleanup_database())
    except KeyboardInterrupt:
        print("\n👋 Cleanup cancelled")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)