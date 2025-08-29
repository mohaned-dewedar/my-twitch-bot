"""
LLM Integration Module

Provides simple interface for calling Language Learning Models
for question generation and other AI tasks.
"""

from .client import LLMClient, LLMConfig

__all__ = ["LLMClient", "LLMConfig"]