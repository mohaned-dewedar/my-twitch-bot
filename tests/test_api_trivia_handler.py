import unittest
from unittest.mock import MagicMock, patch
from trivia.types import ApiTriviaHandler
from data.opentdb import OpenTDBClient
from data.custom import CustomTriviaLoader


class TestApiTriviaHandler(unittest.TestCase):
    def setUp(self):
        # Patch OpenTDBClient and CustomTriviaLoader inside the handler
        patcher_api = patch('data.opentdb.OpenTDBClient')
        patcher_custom = patch('data.custom.CustomTriviaLoader')

        self.mock_api_class = patcher_api.start()
        self.mock_custom_class = patcher_custom.start()
        self.addCleanup(patcher_api.stop)
        self.addCleanup(patcher_custom.stop)

        # Setup mocks
        self.mock_api = self.mock_api_class.return_value
        self.mock_custom = self.mock_custom_class.return_value

        self.mock_api.fetch.return_value = [{
            "question": "What is 2+2?",
            "answer": "4",
            "incorrect_answers": ["2", "3", "5"],
            "all_answers": ["2", "3", "4", "5"],
            "category": "Math",
            "type": "multiple",
            "difficulty": "easy"
        }]
        self.mock_custom.get.return_value = [{
            "question": "Capital of France?",
            "answer": "Paris",
            "options": ["Paris", "Berlin", "Rome"]
        }]

        self.handler = ApiTriviaHandler()

    def test_start_uses_custom_or_api(self):
        question_text = self.handler.start()
        self.assertTrue("?" in question_text)
        self.assertTrue(self.handler.is_active())

    def test_check_answer_correct(self):
        self.handler._question = {"answer": "Paris"}
        self.handler._active = True
        result = self.handler.check_answer("Paris", "Alice")
        self.assertIn("✅", result)
        self.assertFalse(self.handler.is_active())

    def test_check_answer_incorrect(self):
        self.handler._question = {"answer": "Paris"}
        self.handler._active = True
        result = self.handler.check_answer("Rome", "Bob")
        self.assertIn("❌", result)
        self.assertTrue(self.handler.is_active())

    def test_end_returns_answer(self):
        self.handler._question = {"answer": "42"}
        self.handler._active = True
        result = self.handler.end()
        self.assertIn("Trivia ended", result)

    def test_get_help(self):
        help_text = self.handler.get_help()
        self.assertIn("!trivia", help_text)
        self.assertIn("!answer", help_text)


if __name__ == '__main__':
    unittest.main()
