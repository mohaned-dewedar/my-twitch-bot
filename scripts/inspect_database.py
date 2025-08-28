#!/usr/bin/env python3
"""
Database inspection script to view loaded questions and statistics.
Shows question banks, categories, and sample questions.
"""

import asyncio
import json
from typing import Dict, List
from db.database import Database
from config import DATABASE_URL


async def inspect_database():
    """Main function to inspect database contents"""
    print("🔍 CherryBott Database Inspector")
    print("=" * 50)
    
    # Initialize database connection
    db = await Database.init(DATABASE_URL)
    
    try:
        await show_question_banks(db)
        print()
        await show_question_statistics(db)
        print()
        await show_sample_questions(db)
        print()
        await show_category_breakdown(db)
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
    finally:
        await Database.close()


async def show_question_banks(db):
    """Display all question banks and their info"""
    print("📚 QUESTION BANKS")
    print("-" * 30)
    
    async with db.acquire() as conn:
        banks = await conn.fetch("""
            SELECT qb.*, COUNT(q.id) as question_count
            FROM question_banks qb
            LEFT JOIN questions q ON qb.id = q.bank_id
            GROUP BY qb.id
            ORDER BY qb.created_at
        """)
        
        if not banks:
            print("No question banks found.")
            return
            
        for bank in banks:
            print(f"🏦 {bank['name']} ({bank['source_type']})")
            print(f"   📊 {bank['question_count']} questions")
            print(f"   📅 Created: {bank['created_at'].strftime('%Y-%m-%d %H:%M')}")
            if bank['description']:
                print(f"   📝 {bank['description']}")
            print()


async def show_question_statistics(db):
    """Display overall question statistics"""
    print("📊 QUESTION STATISTICS")  
    print("-" * 30)
    
    async with db.acquire() as conn:
        # Total questions
        total = await conn.fetchval("SELECT COUNT(*) FROM questions")
        print(f"📋 Total Questions: {total}")
        
        # By question type
        types = await conn.fetch("""
            SELECT question_type, COUNT(*) as count
            FROM questions 
            GROUP BY question_type 
            ORDER BY count DESC
        """)
        
        print("\n📊 By Question Type:")
        for qtype in types:
            print(f"   {qtype['question_type']}: {qtype['count']} questions")
        
        # By category
        categories = await conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM questions 
            WHERE category IS NOT NULL
            GROUP BY category 
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print(f"\n🏷️ Top Categories:")
        for cat in categories:
            print(f"   {cat['category']}: {cat['count']} questions")
        
        # By difficulty
        difficulties = await conn.fetch("""
            SELECT difficulty, COUNT(*) as count
            FROM questions 
            GROUP BY difficulty 
            ORDER BY difficulty
        """)
        
        print(f"\n⚡ By Difficulty:")
        for diff in difficulties:
            difficulty_name = {1: "Easy", 2: "Medium", 3: "Hard"}.get(diff['difficulty'], f"Level {diff['difficulty']}")
            print(f"   {difficulty_name}: {diff['count']} questions")


async def show_sample_questions(db, limit=3):
    """Display sample questions from each category"""
    print("🎯 SAMPLE QUESTIONS")
    print("-" * 30)
    
    async with db.acquire() as conn:
        # Get sample questions by category
        categories = await conn.fetch("""
            SELECT DISTINCT category 
            FROM questions 
            WHERE category IS NOT NULL 
            ORDER BY category
            LIMIT 5
        """)
        
        for cat_row in categories:
            category = cat_row['category']
            print(f"\n🏷️ {category.upper()} QUESTIONS:")
            
            questions = await conn.fetch("""
                SELECT q.*, qb.name as bank_name
                FROM questions q
                JOIN question_banks qb ON q.bank_id = qb.id
                WHERE q.category = $1
                ORDER BY RANDOM()
                LIMIT $2
            """, category, limit)
            
            for i, q in enumerate(questions, 1):
                print(f"\n   {i}. {q['question']}")
                print(f"      ✅ Answer: {q['correct_answer']}")
                print(f"      📂 Type: {q['question_type']}")
                print(f"      🏦 Source: {q['bank_name']}")
                
                # Show options for MCQ
                if q['question_type'] == 'multiple_choice' and q['answer_options']:
                    options = json.loads(q['answer_options']) if isinstance(q['answer_options'], str) else q['answer_options']
                    emojis = ['🇦', '🇧', '🇨', '🇩']
                    options_str = " ".join([f"{emojis[i]} {opt}" for i, opt in enumerate(options[:4])])
                    print(f"      📝 Options: {options_str}")


async def show_category_breakdown(db):
    """Show detailed breakdown by category and subcategory"""
    print("🗂️ DETAILED CATEGORY BREAKDOWN")
    print("-" * 30)
    
    async with db.acquire() as conn:
        breakdown = await conn.fetch("""
            SELECT 
                category,
                subcategory,
                question_type,
                COUNT(*) as count
            FROM questions
            GROUP BY category, subcategory, question_type
            ORDER BY category, subcategory, question_type
        """)
        
        current_category = None
        current_subcategory = None
        
        for row in breakdown:
            # New category
            if row['category'] != current_category:
                current_category = row['category']
                print(f"\n📁 {current_category or 'UNCATEGORIZED'}")
                current_subcategory = None
                
            # New subcategory  
            if row['subcategory'] != current_subcategory:
                current_subcategory = row['subcategory']
                if current_subcategory:
                    print(f"   📂 {current_subcategory}")
                    
            # Question type count
            indent = "      " if current_subcategory else "   "
            print(f"{indent}• {row['question_type']}: {row['count']} questions")


async def show_recent_activity(db, limit=5):
    """Show recently added questions"""
    print("🕒 RECENT ACTIVITY")
    print("-" * 30)
    
    async with db.acquire() as conn:
        recent = await conn.fetch("""
            SELECT q.question, q.category, qb.name as bank_name, q.created_at
            FROM questions q
            JOIN question_banks qb ON q.bank_id = qb.id
            ORDER BY q.created_at DESC
            LIMIT $1
        """, limit)
        
        if not recent:
            print("No recent questions found.")
            return
            
        for q in recent:
            print(f"📝 {q['question'][:80]}{'...' if len(q['question']) > 80 else ''}")
            print(f"   🏷️ {q['category']} | 🏦 {q['bank_name']} | 📅 {q['created_at'].strftime('%Y-%m-%d %H:%M')}")
            print()


if __name__ == "__main__":
    try:
        asyncio.run(inspect_database())
    except KeyboardInterrupt:
        print("\n👋 Database inspection cancelled")
    except Exception as e:
        print(f"❌ Fatal error: {e}")