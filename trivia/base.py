from abc import ABC, abstractmethod
from typing import Optional, Union, List, Dict, Tuple

class TriviaBase(ABC):
    @abstractmethod
    def get_question(self) -> Optional[dict]:
        """Returns the next trivia question as a structured dict."""
        pass

    @abstractmethod
    def check_answer(self, answer: str, username: Optional[str] = None) -> Tuple[bool, str]:
        """Checks the answer and returns (is_correct: bool, response_message: str)."""
        pass

    @abstractmethod
    def is_active(self) -> bool:
        """Returns True if a trivia session is active."""
        pass

    @abstractmethod
    def start(self) -> str:
        """Begins a trivia round and returns a prompt string."""
        pass

    @abstractmethod
    def end(self) -> str:
        """Ends current trivia session and returns the correct answer."""
        pass

    @abstractmethod
    def get_help(self) -> str:
        """Returns help message for commands or usage."""
        pass