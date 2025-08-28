from typing import Optional, Dict, List
from .opentdb_client import OpenTDBClient


class ApiQuestionQueue:
    """
    Question queue that pre-loads trivia questions for better performance.
    
    Maintains a buffer of questions fetched from OpenTDB API to avoid
    delays when users request questions. Automatically refills when empty.
    """
    
    def __init__(self, preload_amount: int = 10, qtype: str = "multiple", 
                 category: str = None, difficulty: str = "easy"):
        """
        Initialize question queue with configuration.
        
        Args:
            preload_amount: Number of questions to keep in buffer
            qtype: Question type for all questions in queue
            category: Category filter or None for mixed categories
            difficulty: Difficulty level for all questions
        """
        self.client = OpenTDBClient()
        self.qtype = qtype
        self.category = category
        self.difficulty = difficulty
        self.preload_amount = preload_amount
        self.queue: List[Dict] = []
        
        print(f"[INFO] Question queue initialized: {preload_amount} {difficulty} {qtype} questions"
              + (f" from {category}" if category else " from all categories"))

    def _refill(self) -> None:
        """
        Refill the question buffer by fetching from API.
        
        Called automatically when queue is empty. May result in
        fewer questions than requested if API has limitations.
        """
        print(f"[INFO] Refilling question buffer (target: {self.preload_amount})...")
        
        new_questions = self.client.fetch(
            amount=self.preload_amount,
            qtype=self.qtype,
            category=self.category,
            difficulty=self.difficulty
        )
        
        self.queue.extend(new_questions)
        print(f"[INFO] Buffer refilled with {len(new_questions)} questions "
              f"(total: {len(self.queue)})")

    def get_next(self) -> Optional[Dict]:
        """
        Get the next question from the queue.
        
        Returns:
            Question dictionary or None if no questions available
            
        Note: Automatically refills buffer when empty, but may still
        return None if API is unavailable or has no matching questions.
        """
        if not self.queue:
            self._refill()
            
        if not self.queue:
            print("[WARN] No questions available in queue after refill attempt")
            return None
            
        question = self.queue.pop(0)
        print(f"[DEBUG] Dispensed question, {len(self.queue)} remaining in buffer")
        return question

    def size(self) -> int:
        """Get current number of questions in buffer."""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self.queue) == 0
    
    def clear(self) -> None:
        """Clear all questions from buffer."""
        old_size = len(self.queue)
        self.queue.clear()
        print(f"[INFO] Cleared {old_size} questions from buffer")
    
    def peek(self) -> Optional[Dict]:
        """
        Look at next question without removing it from queue.
        
        Useful for previewing questions or checking queue contents
        without consuming them.
        """
        if not self.queue:
            return None
        return self.queue[0]