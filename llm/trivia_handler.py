import re
import time
from typing import Optional, Tuple
from data.data_loader import SmiteDataLoader
import requests
import random
from html import unescape
import json
import os

class TriviaHandler:

    def __init__(self, data_loader: SmiteDataLoader):
        """
        Initialize the trivia handler with a data loader.
        
        Args:
            data_loader: SmiteDataLoader instance
        """
        self.data_loader = data_loader
        self.trivia_pattern = re.compile(r'\{trivia-ability\}', re.IGNORECASE)
        self.answer_pattern = re.compile(r'\{trivia-([^}]+)\}', re.IGNORECASE)
    def get_random_smite_question(self) -> Optional[dict]:
        """
        Returns a structured question dict for smite trivia:
        {
            "question": "Which god has the ability: Persistent Gust?",
            "correct_answer": "Jing Wei",
            "ability": "Persistent Gust",
            "category": "Smite"
        }
        """
        if self.data_loader.is_trivia_active():
            ability = self.data_loader.get_current_trivia()
            god = self.data_loader.correct_answer
        else:
            ability = self.data_loader.start_trivia()
            god = self.data_loader.correct_answer

        if ability and god:
            return {
                "question": f"Which god has the ability: {ability}?",
                "correct_answer": god,
                "ability": ability,
                "category": "Smite"
            }
        return None

    def handle_message(self, message: str, username: str) -> Optional[str]:
        """
        Handle incoming chat messages for trivia functionality.
        
        Args:
            message: The chat message
            username: The username who sent the message
            
        Returns:
            str: Response message if trivia action was triggered, None otherwise
        """
        # Check for trivia-ability command
        if self.trivia_pattern.search(message):
            return self.start_new_trivia()
        
        # Check for trivia answer
        answer_match = self.answer_pattern.search(message)
        if answer_match and self.data_loader.is_trivia_active():
            god_answer = answer_match.group(1).strip()
            return self.check_answer(god_answer, username)
        
        return None
    
    def get_smite_trivia_question(self) -> Optional[dict]:
        ability = self.data_loader.start_trivia()
        god = self.data_loader.correct_answer
        if ability and god:
            return {
                "question": f"Which god has the ability: {ability}?",
                "correct_answer": god,
                "category": "Smite",
                "all_answers": []  # no multiple choice
            }
        return None
    
    def start_new_trivia(self) -> str:
        """
        Start a new trivia game.
        
        Returns:
            str: Response message with the ability name
        """
        if self.data_loader.is_trivia_active():
            current_ability = self.data_loader.get_current_trivia()
            return f"Trivia already active! Current ability: {current_ability}"
        
        ability = self.data_loader.start_trivia()
        if ability:
            return f"🎯 TRIVIA TIME! Which god has the ability: {ability}? Type {{trivia-god name}} to answer!"
        else:
            return "❌ Failed to start trivia. No data loaded."
    
    def check_answer(self, god_answer: str, username: str) -> str:
        """
        Check a user's answer to the current trivia.
        
        Args:
            god_answer: The user's answer (god name)
            username: The username who answered
            
        Returns:
            str: Response message
        """
        is_correct, correct_answer = self.data_loader.check_trivia_answer(god_answer)
        
        if is_correct:
            self.data_loader.end_trivia()
            return f"🎉 @{username} got it correct! {god_answer} is the right answer!"
        else:
            return f"❌ @{username} - That's not correct. Try again!"
    
    def get_trivia_status(self) -> str:
        """
        Get the current trivia status.
        
        Returns:
            str: Status message
        """
        if self.data_loader.is_trivia_active():
            current_ability = self.data_loader.get_current_trivia()
            return f"Trivia active! Current ability: {current_ability}"
        else:
            return "No trivia currently active."
    
    def force_end_trivia(self) -> str:
        """
        Force end the current trivia game.
        
        Returns:
            str: Response message
        """
        if self.data_loader.is_trivia_active():
            correct_answer = self.data_loader.correct_answer
            self.data_loader.end_trivia()
            return f"Trivia ended! The correct answer was: {correct_answer}"
        else:
            return "No trivia to end."
    
    def get_help_message(self) -> str:
        """
        Get help message for trivia commands.
        
        Returns:
            str: Help message
        """
        return """🎯 SMITE TRIVIA COMMANDS:
• {trivia-ability} - Start a new trivia game
• {trivia-god name} - Answer the current trivia
• Type the exact god name to answer!"""


class GeneralTriviaCache:
    def __init__(self):
        self.url = "https://opentdb.com/api.php"
        self.token_url = "https://opentdb.com/api_token.php?command=request"
        self.token = self.get_token()
        self.last_request_time = 0
        self.min_request_interval = 5  # API enforces 5s/IP
        self.multiple_choice_questions = []
        self.true_false_questions = []
        self.categories = self.load_categories()

    def get_token(self):
        try:
            resp = requests.get(self.token_url)
            data = resp.json()
            if data.get("response_code") == 0:
                print(f"[INFO] Session token acquired.")
                return data["token"]
        except Exception as e:
            print(f"[ERROR] Failed to get token: {e}")
        return None

    def reset_token(self):
        if not self.token:
            return
        try:
            reset_url = f"https://opentdb.com/api_token.php?command=reset&token={self.token}"
            resp = requests.get(reset_url)
            if resp.status_code == 200:
                print("[INFO] Token reset.")
        except Exception as e:
            print(f"[ERROR] Could not reset token: {e}")

    def load_categories(self, json_path="data/trivia_categories.json"):
        """Load trivia categories from JSON file."""
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Failed to load categories: {e}")
        return []

    def get_category_id(self, category):
        """
        Return the OpenTDB category ID for a given category name or ID.
        If not found, return None (no filter).
        """
        if isinstance(category, int):
            return category
        if not category:
            return None
        for cat in self.categories:
            if cat["name"].lower() == category.lower():
                return cat["id"]
        return None  # No match, no filter

    def fetch_questions(self, amount=10, qtype="multiple", category=None):
        # Rate limit
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)

        self.last_request_time = time.time()
        params = {
            "amount": amount,
            "type": qtype,
            "token": self.token
        }

        cat_id = self.get_category_id(category)
        if cat_id:
            params["category"] = cat_id

        try:
            resp = requests.get(self.url, params=params, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"[ERROR] Fetch failed: {e}")
            return

        code = data.get("response_code")
        if code == 4:
            print("[INFO] Token exhausted. Resetting...")
            self.reset_token()
            return self.fetch_questions(amount, qtype, category)
        elif code == 5:
            print("[WARN] Rate limit hit. Waiting and retrying...")
            time.sleep(5)
            return self.fetch_questions(amount, qtype, category)
        elif code != 0:
            print(f"[ERROR] API response code: {code}")
            return

        results = data.get("results", [])
        if not results:
            print("[WARN] No results returned.")
            return

        for item in results:
            try:
                question_data = {
                    "question": unescape(item["question"]),
                    "correct_answer": unescape(item["correct_answer"]),
                    "incorrect_answers": [unescape(ans) for ans in item["incorrect_answers"]],
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                }

                if qtype == "multiple":
                    # Create shuffled list of all answers
                    all_answers = question_data["incorrect_answers"] + [question_data["correct_answer"]]
                    random.shuffle(all_answers)
                    question_data["all_answers"] = all_answers
                    self.multiple_choice_questions.append(question_data)
                else:
                    self.true_false_questions.append(question_data)
            except KeyError as e:
                print(f"[ERROR] Missing key in question data: {e}")
                continue

    def get_multiple_choice(self, category=None) -> dict:
        """
        Return a multiple choice question, optionally filtered by category name or ID.
        """
        if len(self.multiple_choice_questions) < 5:
            self.fetch_questions(qtype="multiple", category=category)

        if not self.multiple_choice_questions:
            raise RuntimeError("No multiple choice questions available. Check API connection.")

        # Filter by category if specified
        filtered_questions = self._filter_by_category(self.multiple_choice_questions, category)
        return random.choice(filtered_questions) if filtered_questions else random.choice(self.multiple_choice_questions)

    def get_true_false(self, category=None) -> dict:
        """
        Return a true/false question, optionally filtered by category name or ID.
        """
        if len(self.true_false_questions) < 5:
            self.fetch_questions(qtype="boolean", category=category)

        if not self.true_false_questions:
            raise RuntimeError("No True/False questions available. Check API connection.")

        # Filter by category if specified
        filtered_questions = self._filter_by_category(self.true_false_questions, category)
        return random.choice(filtered_questions) if filtered_questions else random.choice(self.true_false_questions)

    def _filter_by_category(self, questions, category):
        """Helper method to filter questions by category."""
        if not category:
            return questions
            
        cat_name = None
        if isinstance(category, int):
            for cat in self.categories:
                if cat["id"] == category:
                    cat_name = cat["name"]
                    break
        else:
            cat_name = category
            
        if cat_name:
            return [q for q in questions if q["category"].lower() == cat_name.lower()]
        return questions


if __name__ == "__main__":
    # Example usage of the GeneralTriviaCache
    try:
        trivia_cache = GeneralTriviaCache()
        
        # Get a random multiple choice question
        # q1 = trivia_cache.get_multiple_choice()
        # print("Multiple Choice Question:")
        # print(f"Question: {q1['question']}")
        # print(f"Answers: {q1['all_answers']}")
        # print(f"Correct: {q1['correct_answer']}")
        # print()

        # Get a True/False question
        q2 = trivia_cache.get_true_false()
        print("True/False Question:")
        print(f"Question: {q2['question']}")
        print(f"Correct Answer: {q2['correct_answer']}")
        
    except Exception as e:
        print(f"Error running example: {e}")