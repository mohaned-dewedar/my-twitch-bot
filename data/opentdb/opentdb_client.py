import json
import os
import time
import random
import requests
from html import unescape
from typing import Optional, List, Dict


class OpenTDBClient:
    """
    Client for the Open Trivia Database (OpenTDB) API.
    
    Handles API token management, rate limiting, category caching,
    and question fetching with automatic retries and error handling.
    """
    
    BASE_URL = "https://opentdb.com/api.php"
    TOKEN_URL = "https://opentdb.com/api_token.php?command=request"
    CATEGORY_URL = "https://opentdb.com/api_category.php"
    CATEGORY_JSON_PATH = "data/trivia_categories.json"

    def __init__(self):
        """Initialize client with API token and cached categories."""
        self.token = self._get_token()
        self.last_request_time = 0
        self.min_interval = 5  # Minimum seconds between API requests
        self.categories = self._load_or_fetch_categories()

    def _get_token(self) -> Optional[str]:
        """
        Request a session token from OpenTDB API.
        
        Session tokens prevent duplicate questions within a 6-hour window.
        Returns None if token request fails.
        """
        try:
            res = requests.get(self.TOKEN_URL)
            data = res.json()
            if data.get("response_code") == 0:
                print(f"[INFO] OpenTDB session token acquired")
                return data["token"]
            else:
                print(f"[WARN] Failed to get OpenTDB token: {data}")
                return None
        except Exception as e:
            print(f"[ERROR] Failed to get OpenTDB token: {e}")
            return None

    def _load_or_fetch_categories(self) -> List[Dict[str, str]]:
        """
        Load categories from cache file or fetch from API.
        
        Categories are cached locally to reduce API calls since they
        rarely change. Falls back to API fetch if cache is missing.
        """
        # Try loading from cache first
        if os.path.exists(self.CATEGORY_JSON_PATH):
            try:
                with open(self.CATEGORY_JSON_PATH, "r", encoding="utf-8") as f:
                    categories = json.load(f)
                    print(f"[INFO] Loaded {len(categories)} categories from cache")
                    return categories
            except Exception as e:
                print(f"[WARN] Failed to load cached categories: {e}")

        # Fetch from API and cache
        return self._fetch_and_cache_categories()

    def _fetch_and_cache_categories(self) -> List[Dict[str, str]]:
        """Fetch categories from API and save to cache file."""
        try:
            res = requests.get(self.CATEGORY_URL)
            data = res.json()
            categories = data.get("trivia_categories", [])
            
            # Save to cache
            os.makedirs(os.path.dirname(self.CATEGORY_JSON_PATH), exist_ok=True)
            with open(self.CATEGORY_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(categories, f, indent=2)
            
            print(f"[INFO] Fetched and cached {len(categories)} categories")
            return categories
        except Exception as e:
            print(f"[ERROR] Could not fetch categories: {e}")
            return []

    def get_category_id(self, category: str) -> Optional[int]:
        """
        Convert category name to OpenTDB category ID.
        
        Args:
            category: Category name like "Science: Computers"
            
        Returns:
            Category ID integer or None if not found
        """
        if not category:
            return None
        
        category_lower = category.lower()
        for cat in self.categories:
            if cat["name"].lower() == category_lower:
                return cat["id"]
        return None

    def fetch(self, amount: int = 10, qtype: str = "multiple", 
              category: str = None, difficulty: str = "easy") -> List[Dict]:
        """
        Fetch trivia questions from OpenTDB API.
        
        Args:
            amount: Number of questions (1-50)
            qtype: Question type ("multiple", "boolean", "any")
            category: Category name or None for any category
            difficulty: "easy", "medium", "hard", or "any"
            
        Returns:
            List of parsed question dictionaries with standardized format
        """
        # Rate limiting - ensure minimum interval between requests
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            print(f"[INFO] Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()
        
        # Build request parameters
        params = {
            "amount": min(amount, 50),  # OpenTDB max is 50
            "type": qtype,
            "difficulty": difficulty,
        }
        
        # Add session token if available
        if self.token:
            params["token"] = self.token
            
        # Add category if specified
        cat_id = self.get_category_id(category) if category else None
        if cat_id:
            params["category"] = cat_id

        # Make API request with error handling
        try:
            res = requests.get(self.BASE_URL, params=params, timeout=10)
            data = res.json()
        except Exception as e:
            print(f"[ERROR] OpenTDB API request failed: {e}")
            return []

        return self._handle_response(data, amount, qtype, category, difficulty)

    def _handle_response(self, data: dict, amount: int, qtype: str, 
                        category: str, difficulty: str) -> List[Dict]:
        """
        Handle OpenTDB API response with error codes and retries.
        
        OpenTDB response codes:
        0: Success
        1: No results (invalid parameters)  
        2: Invalid parameter
        3: Token not found
        4: Token empty (need reset)
        5: Rate limit exceeded
        """
        code = data.get("response_code", -1)
        
        if code == 0:
            # Success - parse questions
            questions = []
            for item in data.get("results", []):
                parsed = self._parse_question(item)
                questions.append(parsed)
            print(f"[INFO] Fetched {len(questions)} questions successfully")
            return questions
            
        elif code == 4:
            # Token exhausted - get new token and retry
            print("[INFO] Session token exhausted, requesting new token...")
            self.token = self._get_token()
            return self.fetch(amount, qtype, category, difficulty)
            
        elif code == 5:
            # Rate limit - wait and retry
            print("[WARN] Rate limit exceeded, waiting 5 seconds...")
            time.sleep(5)
            return self.fetch(amount, qtype, category, difficulty)
            
        else:
            # Other errors
            error_messages = {
                1: "No results found for the given parameters",
                2: "Invalid parameter provided",
                3: "Session token not found"
            }
            error_msg = error_messages.get(code, f"Unknown error code: {code}")
            print(f"[ERROR] OpenTDB API error: {error_msg}")
            return []

    def _parse_question(self, item: dict) -> dict:
        """
        Parse raw OpenTDB question into standardized format.
        
        Handles HTML entity decoding and creates shuffled answer options
        for multiple choice questions.
        """
        # Decode HTML entities in all text fields
        correct = unescape(item["correct_answer"])
        incorrect = [unescape(ans) for ans in item.get("incorrect_answers", [])]
        question_text = unescape(item["question"])
        
        # Create shuffled answer list for MCQ
        all_answers = incorrect + [correct]
        random.shuffle(all_answers)
        
        return {
            "question": question_text,
            "correct_answer": correct,
            "incorrect_answers": incorrect,
            "all_answers": all_answers,
            "category": item.get("category", "General"),
            "difficulty": item.get("difficulty", "easy"),
            "type": item.get("type", "multiple")
        }

    def get_all_category_names(self) -> List[str]:
        """Get list of all available category names."""
        return [cat["name"] for cat in self.categories]

    def refresh_categories(self):
        """Force refresh of category cache from API."""
        print("[INFO] Refreshing category cache...")
        self.categories = self._fetch_and_cache_categories()
        print("[INFO] Category cache refreshed successfully")