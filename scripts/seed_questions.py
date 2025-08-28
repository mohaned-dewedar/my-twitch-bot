from db.database import Database
from db.questions import save_question_to_bank
from trivia.types import ApiTriviaHandler, SmiteTriviaHandler
from data.smite import SmiteDataStore
import asyncio

async def seed_from_handler(handler):
    print(f"Seeding from: {handler.__class__.__name__}")
    questions = handler.get_bulk_questions()
    print(f"Found {len(questions)} questions")

    for q in questions:
        await save_question_to_bank(
            question_text=q["question"],
            correct_answer=q["correct_answer"],
            all_answers=q["all_answers"],
            category=q["category"],
            difficulty=q["difficulty"],
            source=q["source"]
        )

async def main():
    await Database.init("postgresql://trivia:trivia-password@localhost/trivia_test")

    smite = SmiteTriviaHandler(SmiteDataStore())
    api = ApiTriviaHandler()

    await seed_from_handler(smite)
    await seed_from_handler(api)

    await Database.close()

if __name__ == "__main__":
    asyncio.run(main())
