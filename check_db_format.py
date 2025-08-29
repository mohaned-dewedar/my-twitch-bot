#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_question_format():
    try:
        conn = await asyncpg.connect('postgresql://trivia:trivia-password@localhost:5432/trivia')
        rows = await conn.fetch('SELECT question_text, answer_options, correct_answer FROM questions LIMIT 3')
        
        print('Sample questions from database:')
        print('=' * 50)
        for i, row in enumerate(rows, 1):
            print(f"Question {i}:")
            print(f"  Text: {row['question_text'][:80]}...")
            print(f"  Options: {row['answer_options']}")
            print(f"  Correct Answer: '{row['correct_answer']}'")
            print()
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_question_format())