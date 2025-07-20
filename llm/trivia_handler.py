import re
from typing import Optional, Tuple
from data.data_loader import SmiteDataLoader


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