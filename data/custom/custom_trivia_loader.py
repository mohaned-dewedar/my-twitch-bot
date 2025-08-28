import json
import os
from typing import List, Dict


class CustomTriviaLoader:
    """
    Loader for custom trivia questions from JSON files.
    
    Supports multiple question types (MCQ, True/False, open-ended) and
    validates question format to ensure compatibility with trivia system.
    """
    
    def __init__(self, trivia_dir: str = "data/trivia"):
        """
        Initialize loader with trivia directory path.
        
        Args:
            trivia_dir: Directory containing JSON trivia files
        """
        self.trivia_dir = trivia_dir
        
        # Categorized questions by type
        self.questions = {
            "mcq": [],          # Multiple choice questions
            "truefalse": [],    # True/false questions  
            "basic": []         # Open-ended/basic questions
        }
        
        self._load_all_json()
        self._log_loading_summary()

    def _load_all_json(self) -> None:
        """
        Load all JSON files from the trivia directory.
        
        Scans the directory for .json files and loads each one.
        Invalid files are logged but don't stop the loading process.
        """
        if not os.path.exists(self.trivia_dir):
            print(f"[WARN] Custom trivia directory not found: {self.trivia_dir}")
            return

        json_files = [f for f in os.listdir(self.trivia_dir) if f.endswith(".json")]
        
        if not json_files:
            print(f"[INFO] No JSON files found in {self.trivia_dir}")
            return

        print(f"[INFO] Loading custom questions from {len(json_files)} JSON files...")
        
        for filename in json_files:
            file_path = os.path.join(self.trivia_dir, filename)
            self._load_file(file_path)

    def _load_file(self, path: str) -> None:
        """
        Load and validate questions from a single JSON file.
        
        Expected JSON format:
        {
            "questions": [
                {
                    "type": "mcq",
                    "question": "Question text?",
                    "answer": "Correct answer",
                    "options": ["Option1", "Option2", "Option3", "Option4"]
                }
            ]
        }
        
        Args:
            path: Path to JSON file to load
        """
        try:
            with open(path, "r", encoding='utf-8') as f:
                data = json.load(f)
                
            questions_data = data.get("questions", [])
            if not questions_data:
                print(f"[WARN] No questions found in {path}")
                return
                
            loaded_count = 0
            for question in questions_data:
                qtype = question.get("type", "basic").lower()
                
                if self._validate_question(question, qtype):
                    self.questions[qtype].append(question)
                    loaded_count += 1
                else:
                    print(f"[WARN] Invalid question in {path}: {question.get('question', 'No question text')}")
            
            print(f"[INFO] Loaded {loaded_count} questions from {os.path.basename(path)}")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in {path}: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to load {path}: {e}")

    def _validate_question(self, question: Dict, qtype: str) -> bool:
        """
        Validate question format based on type.
        
        Args:
            question: Question dictionary to validate
            qtype: Question type ("mcq", "truefalse", "basic")
            
        Returns:
            True if question is valid, False otherwise
        """
        # All questions need these fields
        if not question.get("question") or not question.get("answer"):
            return False
            
        if qtype == "mcq":
            # Multiple choice needs options array with correct answer included
            options = question.get("options")
            if not isinstance(options, list) or len(options) < 2:
                return False
            if question["answer"] not in options:
                return False
                
        elif qtype == "truefalse":
            # True/false questions need answer to be "true" or "false"
            answer = str(question.get("answer")).lower()
            if answer not in ["true", "false"]:
                return False
                
        elif qtype == "basic":
            # Basic questions just need string answer
            if not isinstance(question.get("answer"), str):
                return False
        else:
            # Unknown question type
            return False
            
        return True

    def get(self, qtype: str) -> List[Dict]:
        """
        Get all questions of a specific type.
        
        Args:
            qtype: Question type ("mcq", "truefalse", "basic")
            
        Returns:
            List of questions of the specified type
        """
        return self.questions.get(qtype, [])

    def get_all(self) -> Dict[str, List[Dict]]:
        """Get all questions grouped by type."""
        return self.questions.copy()

    def get_total_count(self) -> int:
        """Get total number of loaded questions across all types."""
        return sum(len(questions) for questions in self.questions.values())

    def get_counts_by_type(self) -> Dict[str, int]:
        """Get count of questions for each type."""
        return {qtype: len(questions) for qtype, questions in self.questions.items()}

    def _log_loading_summary(self) -> None:
        """Log summary of loaded questions."""
        counts = self.get_counts_by_type()
        total = self.get_total_count()
        
        if total == 0:
            print("[INFO] No custom questions loaded")
            return
            
        print(f"[INFO] Custom question summary: {total} total questions")
        for qtype, count in counts.items():
            if count > 0:
                print(f"  - {qtype}: {count} questions")

    def reload(self) -> None:
        """
        Reload all questions from disk.
        
        Useful for picking up changes to JSON files without restarting
        the application.
        """
        print("[INFO] Reloading custom questions...")
        
        # Clear existing questions
        for qtype in self.questions:
            self.questions[qtype].clear()
            
        # Reload from files
        self._load_all_json()
        self._log_loading_summary()
        print("[INFO] Custom questions reloaded successfully")