#!/usr/bin/env python3
"""
Script to load questions from various sources into the database.
Supports Smite data, OpenTDB API, and custom JSON files.
"""

import asyncio
import json
import hashlib
import argparse
from typing import List, Dict

from data.smite import SmiteDataStore
from data.opentdb import OpenTDBClient
from data.custom import CustomTriviaLoader
from data.category_mapping import get_category_group, get_clean_category_name, get_balanced_category_selection
from db.database import Database
from config import DATABASE_URL


class QuestionLoader:
    def __init__(self):
        self.db = None
        
    async def init(self):
        """Initialize database connection"""
        self.db = await Database.init(DATABASE_URL)
        
    async def close(self):
        """Close database connection"""
        await Database.close()

    async def create_question_bank(self, name: str, description: str, source_type: str, 
                                 source_config: Dict = None) -> int:
        """Create a question bank and return its ID"""
        async with self.db.acquire() as conn:
            # First check if it exists
            existing = await conn.fetchrow(
                "SELECT id FROM question_banks WHERE name = $1 AND source_type = $2",
                name, source_type
            )
            if existing:
                # Update the existing bank
                await conn.execute(
                    """UPDATE question_banks 
                       SET description = $3, source_config = $4, last_updated = CURRENT_TIMESTAMP
                       WHERE id = $1""",
                    existing['id'], description, json.dumps(source_config or {})
                )
                return existing['id']
            
            # Create new bank
            result = await conn.fetchrow(
                """INSERT INTO question_banks (name, description, source_type, source_config) 
                   VALUES ($1, $2, $3, $4) 
                   RETURNING id""",
                name, description, source_type, json.dumps(source_config or {})
            )
            return result['id']

    async def clear_questions_in_bank(self, bank_id: int):
        """Remove all questions from a specific bank"""
        async with self.db.acquire() as conn:
            await conn.execute("DELETE FROM questions WHERE bank_id = $1", bank_id)
            
    async def insert_question(self, bank_id: int, question: str, question_type: str,
                            correct_answer: str, answer_options: List[str] = None,
                            category: str = None, subcategory: str = None,
                            difficulty: int = 1, tags: List[str] = None,
                            source_id: str = None, source_data: Dict = None):
        """Insert a single question into the database"""
        async with self.db.acquire() as conn:
            await conn.execute(
                """INSERT INTO questions 
                   (bank_id, question, question_type, correct_answer, answer_options,
                    category, subcategory, difficulty, tags, source_id, source_data)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
                bank_id, question, question_type, correct_answer, 
                json.dumps(answer_options) if answer_options else None,
                category, subcategory, difficulty, tags or [],
                source_id, json.dumps(source_data or {})
            )

    async def load_smite_questions(self):
        """Load Smite ability questions from JSON data"""
        print("Loading Smite questions...")
        
        # Create question bank
        bank_id = await self.create_question_bank(
            name="Smite Gods Abilities",
            description="Questions about Smite god abilities - which god has which ability",
            source_type="smite_data",
            source_config={"file_path": "data/smite_gods_modified.json"}
        )
        
        # Clear existing questions
        await self.clear_questions_in_bank(bank_id)
        
        # Load Smite data
        store = SmiteDataStore()
        if not store.load_data():
            print("Failed to load Smite data")
            return
            
        # Convert abilities to questions
        count = 0
        for god_name, abilities in store.god_to_abilities.items():
            for ability in abilities:
                question_text = f"Which god has the ability: {ability}?"
                await self.insert_question(
                    bank_id=bank_id,
                    question=question_text,
                    question_type="open_ended",
                    correct_answer=god_name,
                    category="Smite",
                    subcategory="abilities",
                    difficulty=2,  # Medium difficulty
                    tags=["smite", "abilities", "gods"],
                    source_id=f"smite_ability_{ability}",
                    source_data={
                        "god": god_name,
                        "ability": ability,
                        "original_format": "ability_to_god_mapping"
                    }
                )
                count += 1
                
        print(f"Loaded {count} Smite questions")

    async def load_opentdb_questions(self, amount: int = 100, use_balanced_selection: bool = True):
        """Load questions from OpenTDB API with improved category organization"""
        print(f"Loading {amount} questions from OpenTDB API...")
        
        client = OpenTDBClient()
        
        # Use balanced category selection or load all main groups
        if use_balanced_selection:
            categories = get_balanced_category_selection(categories_per_group=2)
        else:
            # Manually specify preferred categories
            categories = [
                "General Knowledge", "Science: Computers", "Science & Nature", 
                "Entertainment: Video Games", "Entertainment: Film", "History",
                "Geography", "Sports"
            ]
        
        print(f"Selected categories: {categories}")
        
        # Group categories by main category for better organization
        category_groups = {}
        for category in categories:
            main_group = get_category_group(category)
            if main_group not in category_groups:
                category_groups[main_group] = []
            category_groups[main_group].append(category)
        
        # Create one bank per main category group
        for main_category, group_categories in category_groups.items():
            print(f"\nLoading {main_category} questions from {len(group_categories)} subcategories...")
            
            # Create question bank for this main category
            bank_id = await self.create_question_bank(
                name=f"OpenTDB - {main_category}",
                description=f"Questions from OpenTDB in {main_category} category group",
                source_type="opentdb_api",
                source_config={
                    "main_category": main_category,
                    "subcategories": group_categories,
                    "difficulty": "easy"
                }
            )
            
            # Clear existing questions
            await self.clear_questions_in_bank(bank_id)
            
            total_count = 0
            questions_per_subcategory = max(1, amount // (len(categories) * len(group_categories)))
            
            for subcategory in group_categories:
                print(f"  Loading from {subcategory}...")
                
                # Fetch questions for this subcategory
                questions = client.fetch(
                    amount=questions_per_subcategory, 
                    category=subcategory
                )
                
                count = 0
                for q in questions:
                    # Determine question type
                    qtype = "true_false" if q.get("type") == "boolean" else "multiple_choice"
                    
                    # For boolean questions, normalize answer
                    correct_answer = q["correct_answer"]
                    if qtype == "true_false":
                        correct_answer = correct_answer.lower()
                    
                    # Use our category mapping
                    clean_subcategory = get_clean_category_name(subcategory)
                    
                    await self.insert_question(
                        bank_id=bank_id,
                        question=q["question"],
                        question_type=qtype,
                        correct_answer=correct_answer,
                        answer_options=q.get("all_answers") if qtype == "multiple_choice" else None,
                        category=main_category,  # Main category group
                        subcategory=clean_subcategory,  # Clean subcategory name
                        difficulty={"easy": 1, "medium": 2, "hard": 3}.get(q.get("difficulty", "easy"), 1),
                        tags=["opentdb", main_category.lower(), clean_subcategory.lower()],
                        source_id=f"opentdb_{hashlib.md5(q['question'].encode()).hexdigest()[:8]}",
                        source_data=q
                    )
                    count += 1
                    total_count += 1
                    
                print(f"    Loaded {count} questions from {subcategory}")
                
            print(f"Total loaded for {main_category}: {total_count} questions")

    async def load_custom_questions(self):
        """Load questions from custom JSON files"""
        print("Loading custom questions...")
        
        loader = CustomTriviaLoader()
        
        for qtype, questions in loader.questions.items():
            if not questions:
                continue
                
            print(f"Loading {len(questions)} {qtype} questions...")
            
            # Create question bank
            bank_id = await self.create_question_bank(
                name=f"Custom {qtype.upper()} Questions",
                description=f"Custom {qtype} questions from JSON files",
                source_type="custom_json",
                source_config={"question_type": qtype, "directory": "data/trivia"}
            )
            
            # Clear existing questions
            await self.clear_questions_in_bank(bank_id)
            
            count = 0
            for q in questions:
                # Map question types
                db_qtype = {
                    "mcq": "multiple_choice",
                    "truefalse": "true_false", 
                    "basic": "open_ended"
                }.get(qtype, "open_ended")
                
                # Normalize true/false answers
                correct_answer = q["answer"]
                if db_qtype == "true_false":
                    correct_answer = str(correct_answer).lower()
                elif isinstance(correct_answer, (int, float)):
                    correct_answer = str(correct_answer)
                
                await self.insert_question(
                    bank_id=bank_id,
                    question=q["question"],
                    question_type=db_qtype,
                    correct_answer=correct_answer,
                    answer_options=q.get("options") if db_qtype == "multiple_choice" else None,
                    category=q.get("category", "General"),
                    difficulty=q.get("difficulty", 1),
                    tags=["custom", qtype],
                    source_id=f"custom_{qtype}_{hashlib.md5(q['question'].encode()).hexdigest()[:8]}",
                    source_data=q
                )
                count += 1
                
            print(f"Loaded {count} custom {qtype} questions")

    async def show_stats(self):
        """Show database statistics"""
        async with self.db.acquire() as conn:
            # Question bank stats
            banks = await conn.fetch(
                """SELECT name, source_type, 
                          (SELECT COUNT(*) FROM questions WHERE bank_id = question_banks.id) as question_count
                   FROM question_banks ORDER BY name"""
            )
            
            print("\n=== Question Bank Statistics ===")
            total = 0
            for bank in banks:
                count = bank['question_count']
                total += count
                print(f"{bank['name']}: {count} questions ({bank['source_type']})")
            
            print(f"\nTotal: {total} questions")
            
            # Question type breakdown
            types = await conn.fetch(
                """SELECT question_type, COUNT(*) as count 
                   FROM questions 
                   GROUP BY question_type 
                   ORDER BY count DESC"""
            )
            
            print("\n=== Question Type Breakdown ===")
            for qtype in types:
                print(f"{qtype['question_type']}: {qtype['count']} questions")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Load trivia questions from various sources into the database"
    )
    
    parser.add_argument(
        "--sources", 
        nargs="+", 
        choices=["smite", "custom_json", "opentdb", "all"],
        default=["all"],
        help="Which sources to load questions from (default: all)"
    )
    
    parser.add_argument(
        "--amount", 
        type=int, 
        default=100,
        help="Number of questions to load from OpenTDB API (default: 100)"
    )
    
    parser.add_argument(
        "--balanced", 
        action="store_true",
        help="Use balanced category selection for OpenTDB (default: False)"
    )
    
    parser.add_argument(
        "--stats-only", 
        action="store_true",
        help="Only show database statistics without loading questions"
    )
    
    return parser.parse_args()


async def main():
    args = parse_args()
    
    loader = QuestionLoader()
    await loader.init()
    
    try:
        if args.stats_only:
            await loader.show_stats()
            return
        
        # Determine which sources to load
        sources = args.sources
        if "all" in sources:
            sources = ["smite", "custom_json", "opentdb"]
        
        print(f"Loading questions from sources: {', '.join(sources)}")
        print(f"OpenTDB amount: {args.amount}, Balanced selection: {args.balanced}")
        print("-" * 50)
        
        # Load selected sources
        if "smite" in sources:
            await loader.load_smite_questions()
            
        if "custom_json" in sources:
            await loader.load_custom_questions()
            
        if "opentdb" in sources:
            await loader.load_opentdb_questions(
                amount=args.amount, 
                use_balanced_selection=args.balanced
            )
        
        # Show final statistics
        print("\n" + "="*50)
        await loader.show_stats()
        
    finally:
        await loader.close()


if __name__ == "__main__":
    asyncio.run(main())