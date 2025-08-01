import unittest
import os
from data.data_loader import CustomTriviaLoader


class TestCustomTriviaLoader(unittest.TestCase):
    def setUp(self):
        self.loader = CustomTriviaLoader()

    def test_questions_loaded(self):
        mcq_questions = self.loader.get("mcq")
        self.assertIsInstance(mcq_questions, list)
        if mcq_questions:
            q = mcq_questions[0]
            self.assertIn("question", q)
            self.assertIn("answer", q)
            self.assertTrue(q["answer"] in q.get("options", []))


if __name__ == '__main__':
    unittest.main()