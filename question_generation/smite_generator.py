"""
Smite Question Generator

Specialized question generator for Smite game data. Loads Smite documents
and generates trivia questions using type-specific prompts.
"""

import json
import os
from typing import Dict, List, Any, Optional
from .base_generator import BaseQuestionGenerator
from .prompts import SmitePrompts
from .models import MultipleChoiceQuestion, TrueFalseQuestion, OpenEndedQuestion


class SmiteQuestionGenerator(BaseQuestionGenerator):
    """
    Question generator for Smite game data.
    
    Loads Smite documents (gods, abilities, patches, items, god_changes)
    and generates contextual trivia questions using specialized prompts.
    """
    
    def __init__(self, data_file_path: str = None, llm_client = None):
        """
        Initialize Smite question generator.
        
        Args:
            data_file_path: Path to Smite all_documents.json file
            llm_client: LLM client for question generation (optional)
        """
        super().__init__("smite")
        
        # Default to the standard Smite data location
        if data_file_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_file_path = os.path.join(base_dir, "data", "smite", "all_documents.json")
            
        self.data_file_path = data_file_path
        self.documents_by_type = {}
        self.llm_client = llm_client
        
    def load_data(self) -> bool:
        """
        Load Smite documents from JSON file.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.data_file_path):
                print(f"Error: Data file not found at {self.data_file_path}")
                return False
                
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
                
            # Organize documents by type for efficient access
            self.documents_by_type = {}
            for doc in self.data:
                doc_type = doc.get('type', 'unknown')
                if doc_type not in self.documents_by_type:
                    self.documents_by_type[doc_type] = []
                self.documents_by_type[doc_type].append(doc)
                
            print(f"Loaded {len(self.data)} documents")
            for doc_type, docs in self.documents_by_type.items():
                print(f"  - {doc_type}: {len(docs)} documents")
                
            return True
            
        except Exception as e:
            print(f"Error loading Smite data: {e}")
            return False
            
    def load_prompts(self) -> bool:
        """
        Load prompts for Smite question generation.
        
        Returns:
            bool: True if prompts loaded successfully, False otherwise
        """
        try:
            self.prompts = SmitePrompts.BASE_PROMPTS
            print(f"Loaded prompts for {len(self.prompts)} document types")
            return True
            
        except Exception as e:
            print(f"Error loading prompts: {e}")
            return False
            
    def get_available_types(self) -> List[str]:
        """
        Get list of available document types.
        
        Returns:
            List of document types available in loaded data
        """
        if not self.documents_by_type:
            return []
        return list(self.documents_by_type.keys())
        
    def get_documents_by_type(self, document_type: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get documents of a specific type.
        
        Args:
            document_type: Type of documents to retrieve
            limit: Maximum number of documents to return
            
        Returns:
            List of documents of the specified type
        """
        if document_type not in self.documents_by_type:
            return []
            
        docs = self.documents_by_type[document_type]
        return docs[:limit] if limit else docs
        
    def generate_questions(
        self, 
        document_type: str, 
        count: int = 10,
        question_types: List[str] = None,
        difficulty: str = "medium",
        focus: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for documents of a specific type.
        
        Args:
            document_type: Type of document to generate questions for
            count: Number of questions to generate per document
            question_types: List of question types to generate
            difficulty: Difficulty level (easy/medium/hard)
            focus: Optional focus area (numbers/lore/mechanics/history)
            
        Returns:
            List of generated questions (currently returns placeholder structure)
        """
        if not self.data or document_type not in self.documents_by_type:
            print(f"No data available for document type: {document_type}")
            return []
            
        if question_types is None:
            question_types = ["multiple_choice"]
            
        documents = self.documents_by_type[document_type]
        print(f"Generating questions for {len(documents)} {document_type} documents")
        
        # Placeholder implementation - this is where LLM integration will go
        generated_questions = []
        
        for doc in documents[:count]:  # Limit to requested count for now
            for q_type in question_types:
                # Get the specialized prompt for this document type and question type
                prompt_template = SmitePrompts.get_prompt(
                    document_type=document_type,
                    question_type=q_type,
                    question_count=1,  # Generate 1 question per document for now
                    difficulty=difficulty,
                    focus=focus
                )
                
                # Fill in the content from the document
                prompt = prompt_template.replace("{content}", doc.get('content', ''))
                # Store prompt for future LLM integration
                _ = prompt  # Placeholder for LLM call
                
                # Create placeholder question structure
                # TODO: Replace with actual LLM call
                placeholder_question = self._create_placeholder_question(doc, q_type)
                if placeholder_question and self.validate_question(placeholder_question):
                    generated_questions.append(placeholder_question)
                    
        print(f"Generated {len(generated_questions)} questions")
        return generated_questions
        
    def _create_placeholder_question(self, document: Dict[str, Any], question_type: str) -> Dict[str, Any]:
        """
        Create a placeholder question structure for testing.
        
        Args:
            document: Source document
            question_type: Type of question to create
            
        Returns:
            Placeholder question dictionary
        """
        doc_name = document.get('name', 'Unknown')
        doc_type = document.get('type', 'unknown')
        
        if question_type == "multiple_choice":
            return {
                "question": f"What type of document is '{doc_name}' in the Smite data?",
                "options": [doc_type.title(), "Item", "Relic", "Map"],
                "correct_answer": doc_type.title(),
                "type": "multiple_choice",
                "category": "Entertainment",
                "difficulty": "easy",
                "metadata": {
                    "source_document_id": document.get('id', ''),
                    "source_type": doc_type,
                    "generated": True
                }
            }
        elif question_type == "true_false":
            return {
                "question": f"'{doc_name}' is a {doc_type} in Smite.",
                "correct_answer": "true",
                "type": "true_false", 
                "category": "Entertainment",
                "difficulty": "easy",
                "metadata": {
                    "source_document_id": document.get('id', ''),
                    "source_type": doc_type,
                    "generated": True
                }
            }
        elif question_type == "open_ended":
            return {
                "question": f"What is the name of this {doc_type}? {document.get('content', '')[:100]}...",
                "correct_answer": doc_name,
                "type": "open_ended",
                "category": "Entertainment", 
                "difficulty": "medium",
                "metadata": {
                    "source_document_id": document.get('id', ''),
                    "source_type": doc_type,
                    "generated": True
                }
            }
            
        return None
        
    def generate_questions_for_document(
        self,
        document: Dict[str, Any],
        question_type: str = "multiple_choice",
        count: int = 1,
        difficulty: str = "medium",
        focus: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a single document.
        
        Args:
            document: Single document to generate questions for
            question_type: Type of questions to generate
            count: Number of questions to generate
            difficulty: Difficulty level
            focus: Optional focus area
            
        Returns:
            List of generated questions for this document
        """
        doc_type = document.get('type', 'unknown')
        
        # Get the specialized prompt
        prompt_template = SmitePrompts.get_prompt(
            document_type=doc_type,
            question_type=question_type,
            question_count=count,
            difficulty=difficulty,
            focus=focus
        )
        
        # Fill in the content from the document
        prompt = prompt_template.replace("{content}", document.get('content', ''))
        
        # Use LLM client if available, otherwise return placeholder questions
        if self.llm_client:
            try:
                # Choose appropriate Pydantic model based on question type
                if question_type == "multiple_choice":
                    model_class = MultipleChoiceQuestion
                elif question_type == "true_false":
                    model_class = TrueFalseQuestion
                elif question_type == "open_ended":
                    model_class = OpenEndedQuestion
                else:
                    raise ValueError(f"Unsupported question type: {question_type}")
                
                # Generate structured questions using LLM with Pydantic validation
                # Allow empty responses for documents that aren't suitable for trivia
                pydantic_questions = self.llm_client.generate_structured_list(prompt, model_class, allow_empty=True)
                
                # Handle empty response (LLM decided document isn't suitable for trivia)
                if not pydantic_questions:
                    print(f"📝 LLM skipped {document.get('name', 'Unknown')} (not suitable for trivia)")
                    return []
                
                # Convert Pydantic models to dictionaries for compatibility
                questions = []
                for pq in pydantic_questions:
                    question_dict = pq.model_dump()  # Updated from dict() for Pydantic v2
                    questions.append(question_dict)
                
                print(f"✅ Generated {len(questions)} valid questions for {document.get('name', 'Unknown')}")
                return questions[:count]  # Limit to requested count
                
            except Exception as e:
                print(f"Error generating questions with LLM for {document.get('name', 'Unknown')}: {e}")
                print("Falling back to placeholder questions...")
        
        # Fallback to placeholder questions if no LLM client or LLM fails
        questions = []
        for _ in range(count):
            placeholder = self._create_placeholder_question(document, question_type)
            if placeholder and self.validate_question(placeholder):
                questions.append(placeholder)
                
        return questions
        
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.
        
        Returns:
            Dictionary with data statistics
        """
        if not self.data:
            return {"total_documents": 0, "types": {}}
            
        stats = {
            "total_documents": len(self.data),
            "types": {},
            "data_file": self.data_file_path
        }
        
        for doc_type, docs in self.documents_by_type.items():
            stats["types"][doc_type] = len(docs)
            
        return stats