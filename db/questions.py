from typing import List, Optional
from db.database import Database


async def save_question_to_bank(
    question_text: str,
    correct_answer: str,
    all_answers: Optional[List[str]] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    source: str = "custom"
) -> int:
    pool = await Database.get_pool()
    async with pool.acquire() as conn:
        query = """
        INSERT INTO question_bank (question, correct_answer, all_answers, category, difficulty, source)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id;
        """
        values = (
            question_text,
            correct_answer,
            all_answers,
            category,
            difficulty,
            source
        )
        row = await conn.fetchrow(query, *values)
        return row["id"]
