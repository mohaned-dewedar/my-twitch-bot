import unittest
from unittest.mock import MagicMock
from trivia.manager import TriviaManager  # Adjust path to match your structure
from trivia.base import TriviaBase


class TestTriviaManager(unittest.TestCase):
    def setUp(self):
        self.manager = TriviaManager()
        self.mock_handler = MagicMock(spec=TriviaBase)

    def test_start_trivia_successfully(self):
        self.mock_handler.is_active.return_value = False
        self.mock_handler.start.return_value = "🎯 Started trivia!"
        
        result = self.manager.start_trivia(self.mock_handler)
        self.assertEqual(result, "🎯 Started trivia!")
        self.assertEqual(self.manager.active_handler, self.mock_handler)

    def test_start_when_trivia_active(self):
        # First start
        self.mock_handler.is_active.return_value = False
        self.mock_handler.start.return_value = "Started!"
        self.manager.start_trivia(self.mock_handler)

        # Simulate handler still active
        self.mock_handler.is_active.return_value = True
        self.mock_handler.get_question.return_value = {"question": "What is 2+2?"}

        result = self.manager.start_trivia(self.mock_handler)
        self.assertIn("⚠️ Trivia already active", result)

    def test_submit_answer_when_active(self):
        self.mock_handler.is_active.return_value = True
        self.mock_handler.check_answer.return_value = (True, "✅ Correct!")

        self.manager.active_handler = self.mock_handler
        result = self.manager.submit_answer("Paris", username="Alice")
        self.assertEqual(result, "✅ Correct!")
        self.assertTrue(self.manager._last_answer_correct)
        self.mock_handler.check_answer.assert_called_with("Paris", "Alice")

    def test_submit_answer_when_inactive(self):
        result = self.manager.submit_answer("Zeus", username="Bob")
        self.assertEqual(result, "❌ No active trivia to answer.")

    def test_submit_wrong_answer_when_active(self):
        self.mock_handler.is_active.return_value = True
        self.mock_handler.check_answer.return_value = (False, "❌ @Bob - That's not correct. Try again!")

        self.manager.active_handler = self.mock_handler
        result = self.manager.submit_answer("Wrong", username="Bob")
        self.assertEqual(result, "❌ @Bob - That's not correct. Try again!")
        self.assertFalse(self.manager._last_answer_correct)
        self.assertFalse(self.manager.should_ask_next())
        self.mock_handler.check_answer.assert_called_with("Wrong", "Bob")

    def test_end_trivia_when_active(self):
        self.mock_handler.is_active.return_value = True
        self.mock_handler.end.return_value = "Trivia ended."

        self.manager.active_handler = self.mock_handler
        result = self.manager.end_trivia()
        self.assertEqual(result, "Trivia ended.")
        self.assertIsNone(self.manager.active_handler)

    def test_end_trivia_when_inactive(self):
        result = self.manager.end_trivia()
        self.assertEqual(result, "❌ No active trivia session to end.")

    def test_get_status_when_active(self):
        self.mock_handler.is_active.return_value = True
        self.mock_handler.get_question.return_value = {"question": "What is the capital of France?"}

        self.manager.active_handler = self.mock_handler
        result = self.manager.get_status()
        self.assertIn("📢 Trivia Active:", result)

    def test_get_status_when_inactive(self):
        result = self.manager.get_status()
        self.assertEqual(result, "📭 No trivia currently running.")

    def test_get_help_with_active_handler(self):
        self.mock_handler.get_help.return_value = "Help text here."
        self.manager.active_handler = self.mock_handler
        result = self.manager.get_help()
        self.assertEqual(result, "Help text here.")

    def test_get_help_with_no_handler(self):
        result = self.manager.get_help()
        self.assertIn("No active trivia handler", result)


if __name__ == '__main__':
    unittest.main()
