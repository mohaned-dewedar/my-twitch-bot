"""
Command routing system for Twitch IRC client.

Handles registration and dispatch of chat commands to their respective handlers.
Supports both exact command matches and prefix-based commands with arguments.
"""

from typing import Callable, Dict, Optional, Protocol


class CommandHandler(Protocol):
    """Protocol for command handler functions."""
    def __call__(self, message: str, username: str) -> Optional[str]:
        """Handle a command and return response or None."""
        ...


class CommandRouter:
    """
    Routes Twitch chat commands to their appropriate handlers.
    
    Supports exact command matching (e.g., "!trivia") and prefix matching
    for commands that take arguments (e.g., "!answer <text>").
    """
    
    def __init__(self):
        """Initialize empty command router."""
        self._exact_commands: Dict[str, CommandHandler] = {}
        self._prefix_commands: Dict[str, CommandHandler] = {}
    
    def register_exact_command(self, command: str, handler: CommandHandler) -> None:
        """
        Register a handler for exact command matches.
        
        Args:
            command: Exact command string (e.g., "!trivia", "!giveup")
            handler: Function to handle the command
        """
        self._exact_commands[command.lower()] = handler
    
    def register_prefix_command(self, prefix: str, handler: CommandHandler) -> None:
        """
        Register a handler for prefix-based commands that take arguments.
        
        Args:
            prefix: Command prefix (e.g., "!answer", "!ask")
            handler: Function to handle the command
        """
        self._prefix_commands[prefix.lower()] = handler
    
    def register_commands_batch(self, command_map: Dict[str, CommandHandler]) -> None:
        """
        Register multiple exact commands at once.
        
        Args:
            command_map: Dictionary mapping command strings to handlers
        """
        for command, handler in command_map.items():
            self.register_exact_command(command, handler)
    
    def dispatch_command(self, message: str, username: str) -> Optional[str]:
        """
        Route a message to the appropriate command handler.
        
        Args:
            message: Full chat message from user
            username: Username who sent the message
            
        Returns:
            Response string from handler, or None if no matching command
        """
        message = message.strip()
        message_lower = message.lower()
        
        # Try exact command matches first
        if message_lower in self._exact_commands:
            return self._exact_commands[message_lower](message, username)
        
        # Try prefix matches for commands with arguments
        for prefix, handler in self._prefix_commands.items():
            if message_lower.startswith(prefix):
                return handler(message, username)
        
        # No matching command found
        return None
    
    def get_registered_commands(self) -> Dict[str, list]:
        """
        Get all registered commands for debugging/help purposes.
        
        Returns:
            Dictionary with 'exact' and 'prefix' command lists
        """
        return {
            "exact": list(self._exact_commands.keys()),
            "prefix": list(self._prefix_commands.keys())
        }
    
    def has_command(self, command: str) -> bool:
        """
        Check if a command is registered.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is registered, False otherwise
        """
        command_lower = command.lower()
        
        # Check exact matches
        if command_lower in self._exact_commands:
            return True
            
        # Check if it could match a prefix
        for prefix in self._prefix_commands:
            if command_lower.startswith(prefix):
                return True
                
        return False
    
    def unregister_command(self, command: str) -> bool:
        """
        Remove a command registration.
        
        Args:
            command: Command to unregister
            
        Returns:
            True if command was found and removed, False otherwise
        """
        command_lower = command.lower()
        
        # Try to remove from exact commands
        if command_lower in self._exact_commands:
            del self._exact_commands[command_lower]
            return True
            
        # Try to remove from prefix commands  
        if command_lower in self._prefix_commands:
            del self._prefix_commands[command_lower]
            return True
            
        return False