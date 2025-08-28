"""
Trivia orchestration for managing auto-trivia mode and question flow.

Handles the complex async flow of auto trivia mode, pending questions,
and coordination between different trivia handlers.
"""

import asyncio
import logging
from typing import Optional, Callable, Awaitable
from db.trivia_handlers import GeneralTriviaHandler, SmiteTriviaHandler


LOG = logging.getLogger(__name__)


class TriviaOrchestrator:
    """
    Orchestrates trivia game flow, especially auto-trivia mode.
    
    Manages the complex async flow of:
    - Auto-trivia mode state
    - Pending async question loading  
    - Coordination between different trivia types
    - Automatic question progression
    """
    
    def __init__(self):
        """Initialize trivia orchestrator with default state."""
        # Auto trivia mode state
        self.auto_trivia: bool = False
        self.auto_trivia_type: Optional[str] = None  # "general" | "smite" | None
        
        # Pending question loading (for async operations)
        self._pending_auto_question: Optional[str] = None
        
        # Handlers (will be set externally)
        self.general_handler: Optional[GeneralTriviaHandler] = None
        self.smite_handler: Optional[SmiteTriviaHandler] = None
        
        # Callback for sending messages (will be set externally)
        self._send_message: Optional[Callable[[str], Awaitable[None]]] = None
    
    def set_handlers(self, general: GeneralTriviaHandler, smite: SmiteTriviaHandler) -> None:
        """
        Set the trivia handlers.
        
        Args:
            general: Handler for general knowledge trivia
            smite: Handler for Smite trivia
        """
        self.general_handler = general
        self.smite_handler = smite
    
    def set_message_sender(self, sender: Callable[[str], Awaitable[None]]) -> None:
        """
        Set the message sending callback.
        
        Args:
            sender: Async function to send messages to chat
        """
        self._send_message = sender
    
    def start_auto_trivia(self, trivia_type: str) -> str:
        """
        Start auto trivia mode.
        
        Args:
            trivia_type: "general" or "smite"
            
        Returns:
            Response message to send to chat
        """
        if trivia_type == "smite":
            if not self.smite_handler:
                return "❌ Smite trivia not available. Please try again."
            self.auto_trivia = True
            self.auto_trivia_type = "smite"
            self._pending_auto_question = "smite"
            return "🎯 Starting auto Smite trivia mode..."
            
        elif trivia_type == "general":
            if not self.general_handler:
                return "❌ General trivia not available. Please try again."
            self.auto_trivia = True
            self.auto_trivia_type = "general"
            self._pending_auto_question = "general"
            return "📚 Starting auto general trivia mode..."
            
        else:
            return "❌ Invalid trivia type. Use 'general' or 'smite'."
    
    def start_single_trivia(self, trivia_type: str) -> str:
        """
        Start single trivia question (not auto mode).
        
        Args:
            trivia_type: "general" or "smite"
            
        Returns:
            Response message to send to chat
        """
        if trivia_type == "smite":
            if not self.smite_handler:
                return "❌ Smite trivia not available. Please try again."
            self.auto_trivia = False
            self.auto_trivia_type = None
            self._pending_auto_question = "smite_single"
            return "🎯 Loading Smite trivia question..."
            
        elif trivia_type == "general":
            if not self.general_handler:
                return "❌ General trivia not available. Please try again."
            self.auto_trivia = False
            self.auto_trivia_type = None
            self._pending_auto_question = "general_single"
            return "📚 Loading general trivia question..."
            
        else:
            return "❌ Invalid trivia type. Use 'general' or 'smite'."
    
    def end_trivia_mode(self) -> str:
        """
        End auto trivia mode.
        
        Returns:
            Response message to send to chat
        """
        self.auto_trivia = False
        self.auto_trivia_type = None
        self._pending_auto_question = None
        return "🛑 Auto trivia ended!"
    
    def handle_giveup(self, manager) -> str:
        """
        Handle giveup command with auto-trivia consideration.
        
        Args:
            manager: TriviaManager instance
            
        Returns:
            Response from ending the current question
        """
        answer = manager.end_trivia()
        
        # Queue next question in auto mode
        if self.auto_trivia:
            if self.auto_trivia_type == "smite":
                self._pending_auto_question = "smite"
            else:
                self._pending_auto_question = "general"
        else:
            self.auto_trivia = False
            self.auto_trivia_type = None
            
        return answer
    
    async def handle_pending_questions(self, manager) -> None:
        """
        Process any pending async question loading.
        
        Args:
            manager: TriviaManager instance
        """
        if not self._pending_auto_question or not self._send_message:
            return
            
        pending_type = self._pending_auto_question
        self._pending_auto_question = None
        
        try:
            if pending_type == "smite" and self.smite_handler:
                response = await self.smite_handler.start(force=True)
                self._set_active_handler(manager, self.smite_handler, force=True)
                await self._send_message(response)
                
            elif pending_type == "smite_single" and self.smite_handler:
                response = await self.smite_handler.start()
                self._set_active_handler(manager, self.smite_handler)
                await self._send_message(response)
                
            elif pending_type == "general" and self.general_handler:
                response = await self.general_handler.start(force=True)
                self._set_active_handler(manager, self.general_handler, force=True)
                await self._send_message(response)
                
            elif pending_type == "general_single" and self.general_handler:
                response = await self.general_handler.start()
                self._set_active_handler(manager, self.general_handler)
                await self._send_message(response)
                
        except Exception as e:
            LOG.error(f"Failed to load trivia question: {e}")
            await self._send_message("❌ Failed to load trivia question. Please try again.")
    
    async def handle_auto_progression(self, manager) -> None:
        """
        Handle automatic question progression in auto mode.
        
        Args:
            manager: TriviaManager instance
        """
        if not self.auto_trivia or not manager.should_ask_next() or not self._send_message:
            return
            
        # Wait a moment before asking next question
        await asyncio.sleep(1)
        
        try:
            if self.auto_trivia_type == "smite" and self.smite_handler:
                response = await self.smite_handler.start(force=True)
                self._set_active_handler(manager, self.smite_handler, force=True)
                await self._send_message(response)
                
            elif self.auto_trivia_type == "general" and self.general_handler:
                response = await self.general_handler.start(force=True)
                self._set_active_handler(manager, self.general_handler, force=True)
                await self._send_message(response)
                
        except Exception as e:
            LOG.error(f"Failed to load next auto question: {e}")
            await self._send_message("❌ Auto trivia error. Please try again.")
    
    def _set_active_handler(self, manager, handler, force: bool = False):
        """
        Set the active handler without calling start() (handled async).
        
        Args:
            manager: TriviaManager instance
            handler: Handler to set as active
            force: Whether to override existing active handler
        """
        if manager.active_handler and manager.active_handler.is_active() and not force:
            return  # Don't override active handler unless forced
        manager.active_handler = handler
        manager._last_answer_correct = False
    
    def get_status(self) -> dict:
        """
        Get current orchestrator status.
        
        Returns:
            Dictionary with current auto trivia state
        """
        return {
            "auto_trivia_active": self.auto_trivia,
            "auto_trivia_type": self.auto_trivia_type,
            "has_pending_question": self._pending_auto_question is not None,
            "pending_question_type": self._pending_auto_question
        }