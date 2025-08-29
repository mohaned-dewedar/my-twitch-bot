from trivia.base import TriviaBase
from typing import Optional

from typing import Optional
from trivia.base import TriviaBase

class TriviaManager:
    def __init__(self):
        self.active_handler: Optional[TriviaBase] = None
        self._last_answer_correct = False

    def start_trivia(self, handler: TriviaBase, force: bool = False) -> str:
        if self.active_handler and self.active_handler.is_active() and not force:
            question = self.active_handler.get_question()
            return f"⚠️ Trivia already active: {question['question'] if question else 'unknown question'}"

        self.active_handler = handler
        self._last_answer_correct = False
        return handler.start()

    async def submit_answer(self, answer: str, username: Optional[str] = None, 
                           user_id: Optional[int] = None, channel_id: Optional[int] = None, 
                           session_id: Optional[int] = None) -> str:
        if not self.active_handler or not self.active_handler.is_active():
            return "❌ No active trivia to answer."
        is_correct, message = await self.active_handler.check_answer(
            answer, username, user_id, channel_id, session_id
        )
        # Use the boolean value directly instead of parsing the message
        self._last_answer_correct = is_correct
        return message
    def should_ask_next(self) -> bool:
        # Used by IRCClient to know if next question should be asked in auto mode
        return self._last_answer_correct

    def end_trivia(self) -> str:
        if not self.active_handler or not self.active_handler.is_active():
            return "❌ No active trivia session to end."
        message = self.active_handler.end()
        self.active_handler = None
        return message

    def get_status(self) -> str:
        if self.active_handler and self.active_handler.is_active():
            q = self.active_handler.get_question()
            return f"📢 Trivia Active: {q['question'] if q else 'No current question'}"
        return "📭 No trivia currently running."

    def get_help(self) -> str:
        if self.active_handler:
            return self.active_handler.get_help()
        return "No active trivia handler. Try starting a new round using a trivia source."

        
if __name__ == "__main__":
    # Setup
    from trivia.types import ApiTriviaHandler, SmiteTriviaHandler
    from data.smite import SmiteDataStore
    smite_loader = SmiteDataStore()
    smite_handler = SmiteTriviaHandler(smite_loader)
    api_handler = ApiTriviaHandler()

    manager = TriviaManager()

    # Start a trivia round
    print(manager.start_trivia(api_handler))   # or manager.start_trivia(smite_handler)

    # Submit an answer
    print(manager.submit_answer("Jing Wei", username="Player1"))

    # Get current status
    print(manager.get_status())

    # End the trivia round
    print(manager.end_trivia())