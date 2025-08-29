"""
Base Question Generator

Abstract base class for all question generators. Provides common interface
and shared functionality for generating trivia questions from various data sources.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
import json


class BaseQuestionGenerator(ABC):
    """
    Abstract base class for question generators.
    
    Subclasses must implement methods for loading data, generating questions,
    and formatting output for database storage.
    """
    
    def __init__(self, data_source: str):
        """
        Initialize the generator.
        
        Args:
            data_source: Identifier for the data source (e.g., 'smite', 'opentdb')
        """
        self.data_source = data_source
        self.data = None
        self.prompts = {}
        
    @abstractmethod
    def load_data(self) -> bool:
        """
        Load the source data.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        pass
        
    @abstractmethod
    def load_prompts(self) -> bool:
        """
        Load the type-to-prompt mapping.
        
        Returns:
            bool: True if prompts loaded successfully, False otherwise
        """
        pass
        
    @abstractmethod
    def generate_questions(
        self, 
        document_type: str, 
        count: int = 10,
        question_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a specific document type.
        
        Args:
            document_type: Type of document to generate questions for
            count: Number of questions to generate
            question_types: List of question types ('multiple_choice', 'true_false', 'open_ended')
            
        Returns:
            List of generated questions in standard format
        """
        pass
        
    @abstractmethod
    def get_available_types(self) -> List[str]:
        """
        Get list of available document types for this generator.
        
        Returns:
            List of available document types
        """
        pass
        
    def format_for_database(self, questions: List[Dict[str, Any]], question_bank_name: str) -> Dict[str, Any]:
        """
        Format generated questions for database loading.
        
        Args:
            questions: List of generated questions
            question_bank_name: Name for the question bank
            
        Returns:
            Dictionary formatted for database loading scripts
        """
        formatted = {
            "bank_name": question_bank_name,
            "source_type": self.data_source,
            "description": f"Auto-generated questions from {self.data_source} data",
            "questions": []
        }
        
        for q in questions:
            formatted_q = {
                "question_text": q["question"],
                "correct_answer": q["correct_answer"],
                "question_type": q.get("type", "multiple_choice"),
                "category": q.get("category", "General"),
                "difficulty": q.get("difficulty", "medium"),
                "source_metadata": q.get("metadata", {})
            }
            
            # Add answer options for multiple choice
            if q.get("type") == "multiple_choice" and "options" in q:
                formatted_q["answer_options"] = q["options"]
                
            formatted["questions"].append(formatted_q)
            
        return formatted
        
    def save_questions(self, questions: List[Dict[str, Any]], output_file: str, question_bank_name: str = None) -> bool:
        """
        Save generated questions to JSON file.
        
        Args:
            questions: List of generated questions
            output_file: Path to output JSON file
            question_bank_name: Name for the question bank
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            bank_name = question_bank_name or f"{self.data_source}_generated"
            formatted_data = self.format_for_database(questions, bank_name)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"Error saving questions: {e}")
            return False
            
    def validate_question(self, question: Dict[str, Any]) -> bool:
        """
        Validate a generated question has required fields.
        
        Args:
            question: Question dictionary to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ["question", "correct_answer", "type"]
        
        for field in required_fields:
            if field not in question or not question[field]:
                return False
                
        # Additional validation for multiple choice
        if question["type"] == "multiple_choice":
            if "options" not in question or len(question["options"]) < 2:
                return False
            if question["correct_answer"] not in question["options"]:
                return False
                
        return True