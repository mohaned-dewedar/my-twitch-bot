"""
Database-driven trivia handlers that replace the old JSON/API approach.
These handlers fetch questions from the PostgreSQL database.
"""

import random
import json
from typing import Optional, Dict, List
from trivia.base import TriviaBase
from db.database import Database


class DatabaseTriviaHandler(TriviaBase):
    """Base database trivia handler with common functionality"""
    
    def __init__(self, db: Database):
        self.db = db
        self._current_question = None
        self._active = False
    
    async def _fetch_random_question(self, filters: Dict = None) -> Optional[Dict]:
        """Fetch a random question from database with optional filters"""
        async with self.db.acquire() as conn:
            # Build query with filters
            where_conditions = []
            params = []
            param_count = 0
            
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        param_count += 1
                        if isinstance(value, tuple):
                            # Handle tuple values with IN clause
                            placeholders = ', '.join([f'${param_count + i}' for i in range(len(value))])
                            where_conditions.append(f"{key} IN ({placeholders})")
                            params.extend(value)
                            param_count += len(value) - 1
                        else:
                            where_conditions.append(f"{key} = ${param_count}")
                            params.append(value)
            
            where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            query = f"""
                SELECT q.*, qb.name as bank_name, qb.source_type
                FROM questions q 
                JOIN question_banks qb ON q.bank_id = qb.id
                {where_clause}
                ORDER BY RANDOM() 
                LIMIT 1
            """
            
            row = await conn.fetchrow(query, *params)
            if not row:
                return None
                
            # Convert database row to question dict
            question = {
                'id': row['id'],
                'question': row['question'],
                'question_type': row['question_type'],
                'correct_answer': row['correct_answer'],
                'answer_options': json.loads(row['answer_options']) if row['answer_options'] else None,
                'category': row['category'],
                'subcategory': row['subcategory'],
                'difficulty': row['difficulty'],
                'bank_name': row['bank_name'],
                'source_type': row['source_type']
            }
            
            return question
    
    def _format_mcq_question(self, question: Dict) -> str:
        """Format multiple choice question with emoji options"""
        if not question.get('answer_options'):
            return question['question']
            
        options = question['answer_options']
        emojis = ['🇦', '🇧', '🇨', '🇩']
        
        formatted = f"📚 {question['question']}\n"
        for i, option in enumerate(options[:4]):  # Max 4 options
            formatted += f"{emojis[i]} {option} "
        
        return formatted.strip()
    
    def _check_mcq_answer(self, user_answer: str, question: Dict) -> bool:
        """Check multiple choice answer (supports letter shortcuts)"""
        correct = question['correct_answer'].strip().lower()
        user_input = user_answer.strip().lower()
        
        # Check if user provided letter shortcut (a, b, c, d)
        if len(user_input) == 1 and user_input in 'abcd':
            options = question.get('answer_options', [])
            letter_index = ord(user_input) - ord('a')
            if 0 <= letter_index < len(options):
                return options[letter_index].strip().lower() == correct
        
        # Check direct answer
        return user_input == correct
    
    def get_question(self) -> Optional[Dict]:
        return self._current_question
    
    def is_active(self) -> bool:
        return self._active


class GeneralTriviaHandler(DatabaseTriviaHandler):
    """Handler for general knowledge trivia from OpenTDB and custom questions"""
    
    async def start(self, force: bool = False) -> str:
        if self._active and not force:
            return f"⚠️ Trivia already active: {self._current_question['question'] if self._current_question else 'unknown question'}"
        
        # Fetch random question from non-Smite sources (exclude Smite category)
        async with self.db.acquire() as conn:
            query = """
                SELECT q.*, qb.name as bank_name, qb.source_type
                FROM questions q 
                JOIN question_banks qb ON q.bank_id = qb.id
                WHERE q.category != $1
                ORDER BY RANDOM() 
                LIMIT 1
            """
            
            row = await conn.fetchrow(query, 'Smite')
            if not row:
                return "❌ No general questions available. Try loading questions first."
                
            # Convert database row to question dict
            self._current_question = {
                'id': row['id'],
                'question': row['question'],
                'question_type': row['question_type'],
                'correct_answer': row['correct_answer'],
                'answer_options': json.loads(row['answer_options']) if row['answer_options'] else None,
                'category': row['category'],
                'subcategory': row['subcategory'],
                'difficulty': row['difficulty'],
                'bank_name': row['bank_name'],
                'source_type': row['source_type']
            }
        
        if not self._current_question:
            return "❌ No questions available. Try loading questions first."
        
        self._active = True
        
        # Format question based on type
        if self._current_question['question_type'] == 'multiple_choice':
            return self._format_mcq_question(self._current_question)
        elif self._current_question['question_type'] == 'true_false':
            return f"📚 {self._current_question['question']} (True/False)"
        else:
            return f"📚 {self._current_question['question']}"
    
    def check_answer(self, answer: str, username: Optional[str] = None) -> str:
        if not self._active or not self._current_question:
            return "❌ No active trivia."
        
        user_prefix = f"@{username}" if username else "You"
        qtype = self._current_question['question_type']
        correct_answer = self._current_question['correct_answer']
        
        is_correct = False
        
        if qtype == 'multiple_choice':
            is_correct = self._check_mcq_answer(answer, self._current_question)
        elif qtype == 'true_false':
            is_correct = answer.strip().lower() in ['true', 'false'] and \
                        answer.strip().lower() == correct_answer.lower()
        else:  # open_ended
            is_correct = answer.strip().lower() == correct_answer.strip().lower()
        
        if is_correct:
            self._active = False
            return f"🎉 {user_prefix} got it correct! {correct_answer} is the right answer!"
        else:
            return f"❌ {user_prefix} - That's not correct. Try again!"
    
    def end(self) -> str:
        if not self._current_question:
            return "❌ No active trivia to end."
        
        correct_answer = self._current_question['correct_answer']
        self._active = False
        self._current_question = None
        return f"Trivia ended! The correct answer was: {correct_answer}"
    
    def get_help(self) -> str:
        return """🎲 GENERAL TRIVIA COMMANDS:
• !trivia - Start general knowledge questions
• !answer <your answer> - Submit answers (supports a/b/c/d for MCQ)
• !giveup - End current question and show answer"""


class SmiteTriviaHandler(DatabaseTriviaHandler):
    """Handler for Smite god ability questions"""
    
    async def start(self, force: bool = False) -> str:
        if self._active and not force:
            return f"⚠️ Trivia already active: {self._current_question['question'] if self._current_question else 'unknown question'}"
        
        # Fetch random Smite question
        self._current_question = await self._fetch_random_question({
            'category': 'Smite'
        })
        
        if not self._current_question:
            return "❌ No Smite questions available. Try loading questions first."
        
        self._active = True
        return f"🎯 SMITE TRIVIA! {self._current_question['question']} Type !answer GodName to answer!"
    
    def check_answer(self, answer: str, username: Optional[str] = None) -> str:
        if not self._active or not self._current_question:
            return "❌ No active trivia."
        
        user_prefix = f"@{username}" if username else "You"
        correct_answer = self._current_question['correct_answer']
        
        # Smite god names are case-insensitive
        is_correct = answer.strip().lower() == correct_answer.strip().lower()
        
        if is_correct:
            self._active = False
            return f"🎉 {user_prefix} got it correct! {correct_answer} is the right answer!"
        else:
            return f"❌ {user_prefix} - That's not correct. Try again!"
    
    def end(self) -> str:
        if not self._current_question:
            return "❌ No active trivia to end."
        
        correct_answer = self._current_question['correct_answer']
        self._active = False
        self._current_question = None
        return f"Trivia ended! The correct answer was: {correct_answer}"
    
    def get_help(self) -> str:
        return """🎯 SMITE TRIVIA COMMANDS:
• !trivia smite - Start Smite god ability questions
• !answer GodName - Submit your answer
• !giveup - End current question and show answer"""


# Factory function for easy handler creation
async def create_trivia_handler(handler_type: str, database_url: str) -> DatabaseTriviaHandler:
    """Create and initialize a trivia handler"""
    db = await Database.init(database_url)
    
    if handler_type == "smite":
        return SmiteTriviaHandler(db)
    elif handler_type == "general":
        return GeneralTriviaHandler(db)
    else:
        raise ValueError(f"Unknown handler type: {handler_type}")