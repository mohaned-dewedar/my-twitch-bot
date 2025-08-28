"""
Open Trivia Database (OpenTDB) API client modules.

This package provides:
- OpenTDBClient: Direct API client with rate limiting and error handling
- ApiQuestionQueue: Pre-loading question buffer for better performance

The OpenTDB API provides free access to thousands of trivia questions
across multiple categories and difficulty levels.
"""

from .opentdb_client import OpenTDBClient
from .question_queue import ApiQuestionQueue

__all__ = ['OpenTDBClient', 'ApiQuestionQueue']