import unittest
from unittest.mock import MagicMock
from trivia.types import SmiteTriviaHandler 
from data.data_loader import SmiteDataLoader  


class TestSmiteTriviaHandler(unittest.TestCase):

    def setUp(self):
        # Create a mock SmiteDataLoader with deterministic behavior
        self.mock_loader = MagicMock(spec=SmiteDataLoader)
        self.handler = SmiteTriviaHandler(self.mock_loader)

        # Setup mock data
        self.sample_ability = "Celestial Beam"
        self.sample_god = "Ra"
        self.mock_loader.start_trivia.return_value = self.sample_ability
        self.mock_loader.correct_answer = self.sample_god
        self.mock_loader.check_trivia_answer.side_effect = lambda answer: (
            answer.lower() == self.sample_god.lower(), self.sample_god
        )

    def test_start_trivia_success(self):
        response = self.handler.start()
        self.assertTrue(self.handler.is_active())
        self.assertIn("Which god has the ability", response)
        self.assertIn(self.sample_ability, response)

    def test_start_trivia_already_active(self):
        self.handler.start()
        response = self.handler.start()
        self.assertIn("Trivia already active", response)

    def test_get_question(self):
        self.handler.start()
        question = self.handler.get_question()
        self.assertEqual(question["ability"], self.sample_ability)
        self.assertEqual(question["correct_answer"], self.sample_god)

    def test_check_correct_answer(self):
        self.handler.start()
        response = self.handler.check_answer("Ra", username="TestUser")
        self.assertIn("🎉", response)
        self.assertIn("TestUser", response)
        self.assertFalse(self.handler.is_active())

    def test_check_wrong_answer(self):
        self.handler.start()
        response = self.handler.check_answer("Zeus", username="TestUser")
        self.assertIn("❌", response)
        self.assertTrue(self.handler.is_active())  # Trivia should still be active

    def test_end_trivia(self):
        self.handler.start()
        response = self.handler.end()
        self.assertIn("Trivia ended!", response)
        self.assertFalse(self.handler.is_active())

    def test_end_when_not_active(self):
        response = self.handler.end()
        self.assertEqual(response, "No trivia to end.")

    def test_get_help(self):
        help_text = self.handler.get_help()
        self.assertIn("!trivia smite", help_text)
        self.assertIn("!answer GodName", help_text)


if __name__ == '__main__':
    unittest.main()
