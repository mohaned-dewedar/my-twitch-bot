import json
import random
from difflib import get_close_matches
import requests
from html import unescape
import os
import time
from typing import Optional, Dict , List, Tuple
## NEED TO ORGANIZE THIS FILE, Too many functionalities here

class SmiteDataStore:
    def __init__(self, data_file_path: str = "data/smite_gods_modified.json"):
        self.data_file_path = data_file_path
        self.gods_data = []
        self.ability_to_god = {}
        self.god_to_abilities = {}

    def load_data(self) -> bool:
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.gods_data = data.get('gods', [])

            for god in self.gods_data:
                god_name = god['name']
                abilities = god.get('abilities', [])
                self.god_to_abilities[god_name] = abilities
                for ability in abilities:
                    self.ability_to_god[ability] = god_name

            print(f"Loaded {len(self.gods_data)} gods with {len(self.ability_to_god)} abilities")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to load Smite data: {e}")
            return False

    def get_all_gods(self) -> List[str]:
        return list(self.god_to_abilities.keys())

    def get_all_abilities(self) -> List[str]:
        return list(self.ability_to_god.keys())

    def get_god_by_ability(self, ability: str) -> Optional[str]:
        return self.ability_to_god.get(ability)

    def get_abilities_by_god(self, god_name: str) -> List[str]:
        return self.god_to_abilities.get(god_name, [])

    def search_god(self, query: str) -> Optional[Dict]:
        query = query.lower().strip()
        for god in self.gods_data:
            if query in god['name'].lower():
                return god
        return None

    def search_ability(self, query: str) -> Optional[str]:
        query = query.lower().strip()
        for ability in self.ability_to_god.keys():
            if query in ability.lower():
                return ability
        return None

    def fuzzy_match_god(self, user_input: str) -> Optional[str]:
        user_input = user_input.lower().strip()
        all_gods = self.get_all_gods()
        matches = get_close_matches(user_input, [g.lower() for g in all_gods], n=1, cutoff=0.7)
        if matches:
            for god in all_gods:
                if god.lower() == matches[0]:
                    return god
        return None
class SmiteTriviaEngine:
    def __init__(self, data_store: SmiteDataStore):
        self.data_store = data_store
        self.trivia_active = False
        self.current_trivia = None
        self.correct_answer = None

    def start_trivia(self) -> Optional[str]:
        if not self.data_store.ability_to_god:
            return None

        ability = random.choice(list(self.data_store.ability_to_god.keys()))
        if ability:
            self.current_trivia = ability
            self.correct_answer = self.data_store.get_god_by_ability(ability)
            self.trivia_active = True
            return ability
        return None

    def check_answer(self, user_answer: str) -> Tuple[bool, Optional[str]]:
        if not self.trivia_active or not self.correct_answer:
            return False, None

        is_correct = user_answer.lower().strip() == self.correct_answer.lower().strip()
        return is_correct, self.correct_answer

    def get_current_question(self) -> Optional[dict]:
        if self.trivia_active and self.current_trivia and self.correct_answer:
            return {
                "question": f"Which god has the ability: {self.current_trivia}?",
                "correct_answer": self.correct_answer,
                "ability": self.current_trivia,
                "category": "Smite"
            }
        return None

    def end_trivia(self):
        self.trivia_active = False
        self.current_trivia = None
        self.correct_answer = None

    def is_trivia_active(self) -> bool:
        return self.trivia_active


class ApiQuestionQueue:
    def __init__(self, preload_amount=10, qtype="multiple", category=None):
        self.client = OpenTDBClient()
        self.qtype = qtype
        self.category = category
        self.preload_amount = preload_amount
        self.queue = []

    def _refill(self):
        print(f"[INFO] Refilling API trivia buffer...")
        self.queue.extend(self.client.fetch(
            amount=self.preload_amount,
            qtype=self.qtype,
            category=self.category
        ))

    def get_next(self):
        if not self.queue:
            self._refill()
        if not self.queue:
            return None
        return self.queue.pop(0)

    def size(self):
        return len(self.queue)


class OpenTDBClient:
    BASE_URL = "https://opentdb.com/api.php"
    TOKEN_URL = "https://opentdb.com/api_token.php?command=request"
    CATEGORY_URL = "https://opentdb.com/api_category.php"
    CATEGORY_JSON_PATH = "data/trivia_categories.json"

    def __init__(self):
        self.token = self._get_token()
        self.last_request_time = 0
        self.min_interval = 5
        self.categories = self._load_or_fetch_categories()

    def _get_token(self) -> Optional[str]:
        try:
            res = requests.get(self.TOKEN_URL)
            data = res.json()
            return data["token"] if data.get("response_code") == 0 else None
        except Exception as e:
            print(f"[ERROR] Failed to get token: {e}")
            return None

    def _load_or_fetch_categories(self) -> List[Dict[str, str]]:
        if os.path.exists(self.CATEGORY_JSON_PATH):
            try:
                with open(self.CATEGORY_JSON_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load cached categories: {e}")

        # Fetch from API
        try:
            res = requests.get(self.CATEGORY_URL)
            data = res.json()
            categories = data.get("trivia_categories", [])
            os.makedirs(os.path.dirname(self.CATEGORY_JSON_PATH), exist_ok=True)
            with open(self.CATEGORY_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(categories, f, indent=2)
            return categories
        except Exception as e:
            print(f"[ERROR] Could not fetch categories: {e}")
            return []

    def get_category_id(self, category: str) -> Optional[int]:
        if not category:
            return None
        for cat in self.categories:
            if cat["name"].lower() == category.lower():
                return cat["id"]
        return None

    def fetch(self, amount=10, qtype="multiple", category=None) -> List[Dict]:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

            self.last_request_time = time.time()
            params = {
                "amount": amount,
                "type": qtype,
                "token": self.token,
                "difficulty": "easy"  # Always use easy difficulty
            }

            cat_id = self.get_category_id(category)
            if cat_id:
                params["category"] = cat_id

            try:
                res = requests.get(self.BASE_URL, params=params, timeout=10)
                data = res.json()
            except Exception as e:
                print(f"[ERROR] Fetch failed: {e}")
                return []

            code = data.get("response_code")
            if code == 4:
                print("[INFO] Token exhausted. Resetting...")
                self.token = self._get_token()
                return self.fetch(amount, qtype, category)
            elif code == 5:
                print("[WARN] Rate limit hit. Retrying...")
                time.sleep(5)
                return self.fetch(amount, qtype, category)
            elif code != 0:
                print(f"[ERROR] Unexpected response code: {code}")
                return []

            # Ensure each question has 'correct_answer' and 'incorrect_answers' keys
            questions = []
            for item in data.get("results", []):
                q = self._parse_question(item)
                # Guarantee keys
                if "correct_answer" not in q and "answer" in q:
                    q["correct_answer"] = q["answer"]
                if "incorrect_answers" not in q:
                    q["incorrect_answers"] = item.get("incorrect_answers", [])
                questions.append(q)
            return questions

    def _parse_question(self, item: dict) -> dict:
        correct = unescape(item["correct_answer"])
        incorrect = [unescape(ans) for ans in item["incorrect_answers"]]
        all_answers = incorrect + [correct]
        random.shuffle(all_answers)
        return {
            "question": unescape(item["question"]),
            "correct_answer": correct,
            "incorrect_answers": incorrect,
            "all_answers": all_answers,
            "category": item["category"],
            "difficulty": item["difficulty"],
            "type": item["type"]
        }

    def get_all_category_names(self) -> List[str]:
        return [cat["name"] for cat in self.categories]

    def refresh_categories(self):
        """Force re-fetch categories and update cache."""
        try:
            res = requests.get(self.CATEGORY_URL)
            data = res.json()
            categories = data.get("trivia_categories", [])
            os.makedirs(os.path.dirname(self.CATEGORY_JSON_PATH), exist_ok=True)
            with open(self.CATEGORY_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(categories, f, indent=2)
            self.categories = categories
            print("[INFO] Trivia categories refreshed.")
        except Exception as e:
            print(f"[ERROR] Failed to refresh categories: {e}")


class CustomTriviaLoader:
    def __init__(self, trivia_dir="data/trivia"):
        self.trivia_dir = trivia_dir
        self.questions = {
            "mcq": [],
            "truefalse": [],
            "basic": []
        }
        self._load_all_json()

    def _load_all_json(self):
        if not os.path.exists(self.trivia_dir):
            print(f"[WARN] Custom trivia directory missing: {self.trivia_dir}")
            return

        for filename in os.listdir(self.trivia_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.trivia_dir, filename)
                self._load_file(path)

    def _load_file(self, path: str):
        try:
            with open(path, "r", encoding='utf-8') as f:
                data = json.load(f)
                for q in data.get("questions", []):
                    qtype = q.get("type", "basic").lower()
                    if self._validate(q, qtype):
                        self.questions[qtype].append(q)
        except Exception as e:
            print(f"[ERROR] Loading {path} failed: {e}")

    def _validate(self, q: Dict, qtype: str) -> bool:
        if qtype == "mcq":
            return (
                isinstance(q.get("options"), list) and
                q["answer"] in q["options"]
            )
        elif qtype == "truefalse":
            return str(q.get("answer")).lower() in ["true", "false"]
        elif qtype == "basic":
            return isinstance(q.get("answer"), str)
        return False

    def get(self, qtype: str) -> List[Dict]:
        return self.questions.get(qtype, [])


if __name__ == "__main__":
    store = SmiteDataStore()
    if store.load_data():
        engine = SmiteTriviaEngine(store)
        ability = engine.start_trivia()
        if ability:
            print(engine.get_current_question())
            is_correct, answer = engine.check_answer("Zeus")
            print("Correct!" if is_correct else f"Wrong. It was {answer}")


    # client = OpenTDBClient()
    # print(client.get_all_category_names())       # List of strings
    # print(client.get_category_id("Science: Computers"))  # e.g., 18

    # question = client.fetch(amount=1, qtype="multiple")[0]
    # print(question["question"])
    # print(question["all_answers"])
