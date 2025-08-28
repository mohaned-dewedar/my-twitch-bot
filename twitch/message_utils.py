"""
Message processing utilities for Twitch IRC client.

Provides functions for cleaning and formatting messages for Twitch chat,
including markdown removal and text processing.
"""

import re


def strip_markdown(text: str) -> str:
    """
    Remove markdown formatting for Twitch chat compatibility.
    
    Twitch chat doesn't support markdown, so this function strips
    common markdown elements while preserving the readable text.
    
    Args:
        text: Text that may contain markdown formatting
        
    Returns:
        Clean text with markdown formatting removed
    """
    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Remove code blocks and inline code
    text = re.sub(r'```[^`]*```', '', text)         # ```code blocks```
    text = re.sub(r'`([^`]+)`', r'\1', text)        # `inline code`
    
    # Remove links but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url)
    text = re.sub(r'<([^>]+)>', r'\1', text)              # <url>
    
    # Remove headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove bullet points and numbering
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', ' ', text)  # Multiple newlines to single space
    text = re.sub(r'\s+', ' ', text)      # Multiple spaces to single space
    
    return text.strip()


def format_irc_message(channel: str, message: str) -> str:
    """
    Format a message for sending to IRC.
    
    Args:
        channel: IRC channel name (without #)
        message: Message content to send
        
    Returns:
        Properly formatted IRC PRIVMSG command
    """
    return f"PRIVMSG #{channel} :{message}"


def extract_command_and_args(message: str) -> tuple[str, str]:
    """
    Extract command and arguments from a chat message.
    
    Args:
        message: Full chat message starting with command
        
    Returns:
        Tuple of (command, remaining_args)
        
    Example:
        extract_command_and_args("!trivia auto smite") 
        -> ("!trivia auto smite", "")
        
        extract_command_and_args("!answer The Great Wall")
        -> ("!answer", "The Great Wall")
    """
    message = message.strip()
    
    # Handle commands that take arguments
    if message.startswith("!answer "):
        return ("!answer", message[8:])  # Remove "!answer "
    elif message.startswith("!ask "):
        return ("!ask", message[5:])     # Remove "!ask "
    elif message.startswith("!chat "):
        return ("!chat", message[6:])    # Remove "!chat "
    else:
        # For other commands, return the full command
        return (message.lower(), "")


def is_valid_twitch_message(message: str) -> bool:
    """
    Check if a message is valid for sending to Twitch.
    
    Args:
        message: Message to validate
        
    Returns:
        True if message is valid, False otherwise
    """
    if not message or not message.strip():
        return False
        
    # Check for basic validity
    if len(message.strip()) == 0:
        return False
        
    return True