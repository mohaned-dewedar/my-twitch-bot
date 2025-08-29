"""
LLM Configuration

Provides configuration management for ollama and common presets.
"""

import os
from .client import LLMConfig


class LLMPresets:
    """Common LLM configuration presets."""
    
    @staticmethod
    def ollama_local(model: str = "granite3.2:8b") -> LLMConfig:
        """Local Ollama configuration."""
        return LLMConfig(
            host="http://localhost:11434",
            model=model,
            temperature=0.7,
            num_predict=1000
        )
    
    @staticmethod
    def ollama_creative(model: str = "llama3.2") -> LLMConfig:
        """Creative writing configuration with higher temperature."""
        return LLMConfig(
            host="http://localhost:11434",
            model=model,
            temperature=0.9,
            num_predict=1500
        )
    
    @staticmethod
    def ollama_precise(model: str = "granite3.2:8b") -> LLMConfig:
        """Precise/factual configuration with lower temperature."""
        return LLMConfig(
            host="http://localhost:11434",
            model=model,
            temperature=0.3,
            num_predict=800
        )


def load_config_from_env() -> LLMConfig:
    """
    Load LLM configuration from environment variables.
    
    Environment variables:
    - OLLAMA_HOST: Ollama host URL
    - LLM_MODEL: Model name to use
    - LLM_TEMPERATURE: Temperature setting (0.0-1.0)
    - LLM_NUM_PREDICT: Number of tokens to generate
    
    Returns:
        LLMConfig from environment variables or defaults
    """
    return LLMConfig(
        host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        model=os.getenv("LLM_MODEL", "granite3.2:8b"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        num_predict=int(os.getenv("LLM_NUM_PREDICT", "1000"))
    )


def get_question_generation_config() -> LLMConfig:
    """
    Get optimized configuration for question generation.
    
    Returns:
        LLMConfig optimized for generating trivia questions
    """
    # Check if custom config is set via environment
    if os.getenv("LLM_MODEL"):
        config = load_config_from_env()
        # Optimize for question generation
        config.temperature = 0.4  # Balance creativity with consistency
        config.num_predict = 1200   # Enough for multiple questions
        return config
    
    # Default to precise Ollama configuration
    return LLMPresets.ollama_precise()


# Configuration examples
SETUP_EXAMPLES = {
    "description": "Local Ollama instance",
    "setup": [
        "1. Install Ollama: https://ollama.ai/",
        "2. Start service: ollama serve",
        "3. Pull model: ollama pull llama3.2"
    ],
    "config": LLMPresets.ollama_local()
}