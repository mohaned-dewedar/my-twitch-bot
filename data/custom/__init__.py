"""
Custom trivia question loader from JSON files.

This package provides:
- CustomTriviaLoader: Loads and validates custom questions from JSON files

Supports multiple question types:
- MCQ: Multiple choice with 2+ options
- True/False: Boolean questions  
- Basic: Open-ended questions with string answers
"""

from .custom_trivia_loader import CustomTriviaLoader

__all__ = ['CustomTriviaLoader']