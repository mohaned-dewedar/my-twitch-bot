"""
LLM Client

Simple interface for making calls to Language Learning Models using ollama.
"""

import json
import ollama
from typing import Dict, Any, Optional, List, Type, TypeVar, Union
from dataclasses import dataclass
import logging
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    host: str = "http://localhost:11434"
    model: str = "llama3.2"
    temperature: float = 0.7
    num_predict: int = 1000
    

class LLMClient:
    """
    Simple client for making LLM requests using ollama.
    """
    
    def __init__(self, config: LLMConfig = None):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration settings
        """
        self.config = config or LLMConfig()
        self.client = ollama.Client(host=self.config.host)
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
            
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using ollama.
        
        Args:
            prompt: Input prompt for the LLM
            **kwargs: Additional parameters to override config
            
        Returns:
            Generated text response
            
        Raises:
            LLMError: If the request fails
        """
        try:
            options = {
                'temperature': kwargs.get('temperature', self.config.temperature),
                'num_predict': kwargs.get('num_predict', self.config.num_predict)
            }
            
            response = self.client.generate(
                model=kwargs.get('model', self.config.model),
                prompt=prompt,
                stream=False,
                options=options
            )
            
            return response.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMError(f"LLM request failed: {e}")
            
    def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate JSON response from LLM.
        
        Args:
            prompt: Input prompt requesting JSON output
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
            
        Raises:
            LLMError: If response is not valid JSON
        """
        # Add JSON format instruction to prompt
        json_prompt = f"{prompt}\n\nIMPORTANT: Respond with valid JSON only, no additional text."
        
        response = self.generate(json_prompt, **kwargs)
        
        # Try to extract JSON from response
        try:
            # Look for JSON in response (handle cases where LLM adds extra text)
            # Check for array first
            array_start = response.find('[')
            array_end = response.rfind(']') + 1
            
            if array_start >= 0 and array_end > array_start:
                json_text = response[array_start:array_end]
            else:
                # Fallback to object
                obj_start = response.find('{')
                obj_end = response.rfind('}') + 1
                
                if obj_start >= 0 and obj_end > obj_start:
                    json_text = response[obj_start:obj_end]
                else:
                    json_text = response
                
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise LLMError(f"Invalid JSON response: {e}")
    
    def generate_structured(self, prompt: str, model_class: Type[T], **kwargs) -> T:
        """
        Generate structured response using Pydantic model.
        
        Args:
            prompt: Input prompt requesting structured output
            model_class: Pydantic model class to parse response into
            **kwargs: Additional parameters
            
        Returns:
            Instance of the specified Pydantic model
            
        Raises:
            LLMError: If response cannot be parsed into the model
        """
        # Add model schema to prompt for better results
        schema_prompt = f"""{prompt}

RESPONSE FORMAT:
Return a valid JSON object that matches this schema:
{model_class.schema_json(indent=2)}

IMPORTANT: Return only valid JSON, no additional text."""

        try:
            json_response = self.generate_json(schema_prompt, **kwargs)
            return model_class(**json_response)
            
        except ValidationError as e:
            logger.error(f"Failed to validate response against {model_class.__name__}: {e}")
            raise LLMError(f"Response validation failed: {e}")
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise LLMError(f"Structured generation failed: {e}")
    
    def generate_structured_list(self, prompt: str, model_class: Type[T], allow_empty: bool = False, **kwargs) -> List[T]:
        """
        Generate list of structured responses using Pydantic model.
        
        Args:
            prompt: Input prompt requesting structured output
            model_class: Pydantic model class to parse response items into
            allow_empty: Whether to allow empty responses (returns empty list instead of error)
            **kwargs: Additional parameters
            
        Returns:
            List of instances of the specified Pydantic model (can be empty if allow_empty=True)
            
        Raises:
            LLMError: If response cannot be parsed into the model list (unless allow_empty=True)
        """
        # Add model schema to prompt for better results
        empty_instruction = "\nIf the content is not suitable for interesting trivia questions, return an empty array: []" if allow_empty else ""
        
        schema_prompt = f"""{prompt}

RESPONSE FORMAT:
Return a valid JSON array of objects that match this schema:
{model_class.schema_json(indent=2)}{empty_instruction}

IMPORTANT: Return only valid JSON array, no additional text."""

        try:
            json_response = self.generate_json(schema_prompt, **kwargs)
            
            # Handle empty responses
            if not json_response or (isinstance(json_response, list) and len(json_response) == 0):
                if allow_empty:
                    logger.info("LLM returned empty response (allowed)")
                    return []
                else:
                    raise LLMError("Empty response not allowed")
            
            # Ensure we have a list
            if not isinstance(json_response, list):
                json_response = [json_response]
            
            # Parse each item in the list
            structured_items = []
            for item in json_response:
                try:
                    structured_items.append(model_class(**item))
                except ValidationError as e:
                    logger.warning(f"Skipping invalid item in response: {e}")
                    continue
            
            # Check if we ended up with no valid items
            if not structured_items:
                if allow_empty:
                    logger.info("No valid items found, returning empty list (allowed)")
                    return []
                else:
                    raise LLMError("No valid items found in response")
                
            return structured_items
            
        except ValidationError as e:
            logger.error(f"Failed to validate response list against {model_class.__name__}: {e}")
            raise LLMError(f"Response validation failed: {e}")
        except Exception as e:
            logger.error(f"Structured list generation failed: {e}")
            raise LLMError(f"Structured list generation failed: {e}")
            
    def health_check(self) -> bool:
        """
        Check if ollama service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            models = self.client.list()
            return len(models.get('models', [])) >= 0
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
            
    def get_models(self) -> List[str]:
        """
        Get available models.
        
        Returns:
            List of model names
        """
        try:
            response = self.client.list()
            models = response.get('models', [])
            return [model.get('name', '') for model in models]
            
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []


class LLMError(Exception):
    """Exception raised for LLM-related errors."""
    pass