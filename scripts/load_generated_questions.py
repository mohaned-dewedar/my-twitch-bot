#!/usr/bin/env python3
"""
Script to load auto-generated Smite questions from batch JSON files into the database.
"""

import asyncio
import json
import glob
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict

from db.database import Database
from config import DATABASE_URL


class GeneratedQuestionLoader:
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

    def map_category(self, original_category: str) -> str:
        """Map generated categories to database categories"""
        category_mapping = {
            "Smite Stats": "Entertainment",
            "Smite Gameplay": "Entertainment", 
            "Greek Mythology": "Culture",
            "Mythology": "Culture",
            "Gaming": "Entertainment",
            "Entertainment": "Entertainment"
        }
        return category_mapping.get(original_category, "Entertainment")

    def map_difficulty(self, difficulty_str: str) -> int:
        """Map difficulty string to integer"""
        difficulty_mapping = {
            "easy": 1,
            "medium": 2, 
            "hard": 3
        }
        return difficulty_mapping.get(difficulty_str.lower(), 2)

    async def load_batch_questions(self, generated_questions_dir: str = "generated_questions"):
        """Load questions from all batch JSON files"""
        print(f"Loading generated questions from {generated_questions_dir}/...")
        
        # Create question bank
        bank_id = await self.create_question_bank(
            name="Smite Auto-Generated Questions",
            description="Auto-generated multiple choice questions from Smite data using LLM",
            source_type="smite_auto_generated",
            source_config={
                "generator": "granite3.2:8b",
                "generation_date": "2025-08-29",
                "source_documents": "smite god and ability data"
            }
        )
        
        # Clear existing questions
        await self.clear_questions_in_bank(bank_id)
        
        # Find all batch JSON files
        batch_files = glob.glob(f"{generated_questions_dir}/*batch*.json")
        if not batch_files:
            print(f"No batch files found in {generated_questions_dir}/")
            return
            
        print(f"Found {len(batch_files)} batch files to process")
        
        total_questions = 0
        for batch_file in sorted(batch_files):
            print(f"Processing {Path(batch_file).name}...")
            
            try:
                with open(batch_file, 'r') as f:
                    batch_data = json.load(f)
                    
                questions = batch_data.get('questions', [])
                file_count = 0
                
                for q in questions:
                    # Extract question data
                    question_text = q['question']
                    options = q['options']
                    correct_answer = q['correct_answer']
                    correct_letter = q.get('correct_letter', '')
                    category = q.get('category', 'Entertainment')
                    difficulty = q.get('difficulty', 'medium')
                    metadata = q.get('metadata', {})
                    
                    # Map to database format
                    db_category = self.map_category(category)
                    db_difficulty = self.map_difficulty(difficulty)
                    
                    # Create source ID
                    source_id = f"generated_{hashlib.md5(question_text.encode()).hexdigest()[:12]}"
                    
                    # Determine subcategory from metadata
                    doc_type = metadata.get('source_document_type', 'unknown')
                    subcategory = f"smite_{doc_type}"
                    
                    # Create comprehensive source data
                    source_data = {
                        **metadata,
                        'batch_file': Path(batch_file).name,
                        'bank_name': batch_data.get('bank_name', ''),
                        'correct_letter': correct_letter,
                        'original_category': category
                    }
                    
                    # Create tags
                    tags = [
                        "smite", 
                        "auto_generated", 
                        doc_type,
                        batch_data.get('source_type', 'smite_auto_generated')
                    ]
                    
                    await self.insert_question(
                        bank_id=bank_id,
                        question=question_text,
                        question_type="multiple_choice",
                        correct_answer=correct_answer,
                        answer_options=options,
                        category=db_category,
                        subcategory=subcategory,
                        difficulty=db_difficulty,
                        tags=tags,
                        source_id=source_id,
                        source_data=source_data
                    )
                    file_count += 1
                    
                print(f"  Loaded {file_count} questions from {Path(batch_file).name}")
                total_questions += file_count
                
            except Exception as e:
                print(f"Error processing {batch_file}: {e}")
                continue
                
        print(f"\nTotal loaded: {total_questions} generated questions")

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
            
            # Auto-generated questions breakdown
            auto_generated = await conn.fetchrow(
                """SELECT COUNT(*) as total_count
                   FROM questions q
                   JOIN question_banks qb ON q.bank_id = qb.id
                   WHERE qb.source_type = 'smite_auto_generated'"""
            )
            
            if auto_generated and auto_generated['total_count'] > 0:
                print(f"\n=== Auto-Generated Questions Breakdown ===")
                print(f"Total auto-generated: {auto_generated['total_count']}")
                
                # Breakdown by subcategory (god vs ability)
                subcats = await conn.fetch(
                    """SELECT subcategory, COUNT(*) as count
                       FROM questions q
                       JOIN question_banks qb ON q.bank_id = qb.id
                       WHERE qb.source_type = 'smite_auto_generated'
                       GROUP BY subcategory
                       ORDER BY count DESC"""
                )
                
                for subcat in subcats:
                    print(f"  {subcat['subcategory']}: {subcat['count']} questions")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Load auto-generated Smite questions from batch JSON files into the database"
    )
    
    parser.add_argument(
        "--generated-dir", 
        default="generated_questions",
        help="Directory containing batch JSON files (default: generated_questions)"
    )
    
    parser.add_argument(
        "--stats-only", 
        action="store_true",
        help="Only show database statistics without loading questions"
    )
    
    return parser.parse_args()


async def main():
    args = parse_args()
    
    loader = GeneratedQuestionLoader()
    await loader.init()
    
    try:
        if args.stats_only:
            await loader.show_stats()
            return
        
        print("Loading auto-generated Smite questions...")
        print("-" * 50)
        
        await loader.load_batch_questions(args.generated_dir)
        
        # Show final statistics
        print("\n" + "="*50)
        await loader.show_stats()
        
    finally:
        await loader.close()


if __name__ == "__main__":
    asyncio.run(main())