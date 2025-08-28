import unittest
import os
from data.smite import SmiteDataStore, SmiteTriviaEngine


class TestSmiteDataLoaderIntegration(unittest.TestCase):
    def setUp(self):
        self.data_path = "data/smite_gods_modified.json"
        self.data_store = SmiteDataStore(self.data_path)
        self.engine = SmiteTriviaEngine(self.data_store)

    def test_file_exists(self):
        self.assertTrue(os.path.exists(self.data_path), "Data file is missing!")

    def test_load_data_successfully(self):
        result = self.data_store.load_data()
        self.assertTrue(result)
        self.assertGreater(len(self.data_store.get_all_gods()), 0)
        self.assertGreater(len(self.data_store.get_all_abilities()), 0)

    def test_start_trivia_returns_valid_ability(self):
        self.data_store.load_data()
        ability = self.engine.start_trivia()
        self.assertIsNotNone(ability)
        self.assertIn(ability, self.data_store.get_all_abilities())

    def test_correct_answer_matches_ability(self):
        self.data_store.load_data()
        ability = self.engine.start_trivia()
        god = self.engine.correct_answer
        self.assertEqual(god, self.data_store.get_god_by_ability(ability))

    def test_check_trivia_answer(self):
        self.data_store.load_data()
        ability = self.engine.start_trivia()
        correct_god = self.engine.correct_answer
        is_correct, result = self.engine.check_answer(correct_god)
        self.assertTrue(is_correct)
        self.assertEqual(result, correct_god)

    def test_fuzzy_match_god(self):
        self.data_store.load_data()
        match = self.data_store.fuzzy_match_god("Ra")
        self.assertIsNotNone(match)
        self.assertEqual(match, "Ra")


if __name__ == '__main__':
    unittest.main()
