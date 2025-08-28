import unittest
from data.opentdb import OpenTDBClient


class TestOpenTDBClient(unittest.TestCase):
    def setUp(self):
        self.client = OpenTDBClient()

    def test_get_token(self):
        self.assertIsNotNone(self.client.token)

    def test_fetch_question(self):
        questions = self.client.fetch(amount=1)
        self.assertEqual(len(questions), 1)
        question = questions[0]
        self.assertIn("question", question)
        self.assertIn("correct_answer", question)
        self.assertIn("all_answers", question)

    def test_get_categories(self):
        names = self.client.get_all_category_names()
        self.assertTrue(len(names) > 0)
        self.assertIn("General Knowledge", names)


if __name__ == '__main__':
    unittest.main()
