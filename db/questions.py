from typing import Optional, Dict
import json
from db.database import Database


async def get_random_question(filters: Optional[Dict] = None) -> Optional[Dict]:
    """Get a random question from the database with optional filters"""
    db = Database.get_instance()
    async with db.acquire() as conn:
        # Build query with filters
        where_conditions = []
        params = []
        param_count = 0
        
        if filters:
            for key, value in filters.items():
                if value is not None:
                    param_count += 1
                    if isinstance(value, tuple):
                        # Handle multiple values (e.g., category IN (...))
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
        return {
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


async def get_question_stats() -> Dict:
    """Get statistics about questions in the database"""
    db = Database.get_instance()
    async with db.acquire() as conn:
        # Total questions
        total = await conn.fetchval("SELECT COUNT(*) FROM questions")
        
        # By category
        categories = await conn.fetch("""
            SELECT category, COUNT(*) as count 
            FROM questions 
            GROUP BY category 
            ORDER BY count DESC
        """)
        
        # By type
        types = await conn.fetch("""
            SELECT question_type, COUNT(*) as count 
            FROM questions 
            GROUP BY question_type 
            ORDER BY count DESC
        """)
        
        # By bank
        banks = await conn.fetch("""
            SELECT qb.name, qb.source_type, COUNT(q.id) as count
            FROM question_banks qb
            LEFT JOIN questions q ON qb.id = q.bank_id
            GROUP BY qb.id, qb.name, qb.source_type
            ORDER BY count DESC
        """)
        
        return {
            'total_questions': total,
            'by_category': [dict(row) for row in categories],
            'by_type': [dict(row) for row in types],
            'by_bank': [dict(row) for row in banks]
        }


async def record_question_attempt(question_id: int, user_id: int, channel_id: int, 
                                is_correct: bool, response_time: float, 
                                user_answer: str) -> int:
    """Record a user's attempt at answering a question"""
    db = Database.get_instance()
    async with db.acquire() as conn:
        query = """
            INSERT INTO user_question_attempts 
            (question_id, user_id, channel_id, is_correct, response_time_seconds, user_answer)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        row = await conn.fetchrow(query, question_id, user_id, channel_id, 
                                 is_correct, response_time, user_answer)
        return row['id']
