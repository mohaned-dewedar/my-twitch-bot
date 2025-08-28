import random
from typing import Optional, Tuple
from .smite_data_store import SmiteDataStore


class SmiteTriviaEngine:
    """Manages Smite trivia game logic and state."""
    
    def __init__(self, data_store: SmiteDataStore):
        self.data_store = data_store
        self.trivia_active = False
        self.current_trivia = None
        self.correct_answer = None

    def start_trivia(self) -> Optional[str]:
        """Start a new trivia round with a random ability."""
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
        """Check if the user's answer is correct."""
        if not self.trivia_active or not self.correct_answer:
            return False, None

        is_correct = user_answer.lower().strip() == self.correct_answer.lower().strip()
        return is_correct, self.correct_answer

    def get_current_question(self) -> Optional[dict]:
        """Get the current trivia question as a structured dict."""
        if self.trivia_active and self.current_trivia and self.correct_answer:
            return {
                "question": f"Which god has the ability: {self.current_trivia}?",
                "correct_answer": self.correct_answer,
                "ability": self.current_trivia,
                "category": "Smite"
            }
        return None

    def end_trivia(self):
        """End the current trivia round."""
        self.trivia_active = False
        self.current_trivia = None
        self.correct_answer = None

    def is_trivia_active(self) -> bool:
        """Check if a trivia round is currently active."""
        return self.trivia_active