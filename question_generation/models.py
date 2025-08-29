"""
Question Generation Models

Pydantic models for structured question generation and validation.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator


class MultipleChoiceQuestion(BaseModel):
    """Model for multiple choice questions."""
    
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_items=2, max_items=6, description="Answer options")
    correct_answer: str = Field(..., description="The correct answer text (must match one of the options)")
    correct_letter: str = Field(..., description="The correct answer letter (A, B, C, D, etc.)")
    type: Literal["multiple_choice"] = Field(default="multiple_choice", description="Question type")
    category: Optional[str] = Field(default="Entertainment", description="Question category")
    difficulty: Optional[str] = Field(default="medium", description="Question difficulty")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('correct_answer')
    def correct_answer_must_be_in_options(cls, v, values):
        """Validate that correct_answer is one of the options."""
        if 'options' in values and v not in values['options']:
            raise ValueError(f"correct_answer '{v}' must be one of the options: {values['options']}")
        return v
    
    @validator('correct_letter')
    def correct_letter_format(cls, v, values):
        """Validate correct_letter format and match with options."""
        if not v or len(v) != 1 or not v.isupper():
            raise ValueError("correct_letter must be a single uppercase letter (A, B, C, D, etc.)")
        
        if 'options' in values:
            expected_index = ord(v) - ord('A')
            if expected_index < 0 or expected_index >= len(values['options']):
                raise ValueError(f"correct_letter '{v}' is out of range for {len(values['options'])} options")
            
            # Optionally validate that the letter corresponds to the correct answer
            if 'correct_answer' in values:
                expected_answer = values['options'][expected_index]
                if values['correct_answer'] != expected_answer:
                    raise ValueError(f"correct_letter '{v}' points to '{expected_answer}' but correct_answer is '{values['correct_answer']}'")
        
        return v


class TrueFalseQuestion(BaseModel):
    """Model for true/false questions."""
    
    question: str = Field(..., description="The question text")
    correct_answer: Literal["true", "false"] = Field(..., description="The correct answer")
    type: Literal["true_false"] = Field(default="true_false", description="Question type")
    category: Optional[str] = Field(default="Entertainment", description="Question category")
    difficulty: Optional[str] = Field(default="medium", description="Question difficulty")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class OpenEndedQuestion(BaseModel):
    """Model for open-ended questions."""
    
    question: str = Field(..., description="The question text")
    correct_answer: str = Field(..., description="The correct answer text")
    type: Literal["open_ended"] = Field(default="open_ended", description="Question type")
    category: Optional[str] = Field(default="Entertainment", description="Question category")
    difficulty: Optional[str] = Field(default="medium", description="Question difficulty")
    acceptable_answers: Optional[List[str]] = Field(default_factory=list, description="Alternative acceptable answers")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class QuestionBank(BaseModel):
    """Model for a collection of questions."""
    
    bank_name: str = Field(..., description="Name of the question bank")
    source_type: str = Field(..., description="Source type (e.g., 'smite', 'opentdb')")
    description: Optional[str] = Field(default="", description="Description of the question bank")
    questions: List[Any] = Field(..., description="List of questions (mixed types)")
    
    @validator('questions')
    def validate_question_types(cls, v):
        """Validate that all questions are valid question types."""
        valid_questions = []
        for question in v:
            if isinstance(question, dict):
                q_type = question.get('type', 'multiple_choice')
                try:
                    if q_type == 'multiple_choice':
                        valid_questions.append(MultipleChoiceQuestion(**question))
                    elif q_type == 'true_false':
                        valid_questions.append(TrueFalseQuestion(**question))
                    elif q_type == 'open_ended':
                        valid_questions.append(OpenEndedQuestion(**question))
                    else:
                        raise ValueError(f"Unknown question type: {q_type}")
                except Exception as e:
                    raise ValueError(f"Invalid question: {e}")
            elif isinstance(question, (MultipleChoiceQuestion, TrueFalseQuestion, OpenEndedQuestion)):
                valid_questions.append(question)
            else:
                raise ValueError(f"Invalid question format: {type(question)}")
        
        return valid_questions


class QuestionGenerationRequest(BaseModel):
    """Model for question generation requests."""
    
    document_type: str = Field(..., description="Type of document (god, ability, etc.)")
    content: str = Field(..., description="Document content to generate questions from")
    question_type: Literal["multiple_choice", "true_false", "open_ended"] = Field(default="multiple_choice")
    question_count: int = Field(default=1, ge=1, le=10, description="Number of questions to generate")
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")
    focus: Optional[str] = Field(default=None, description="Optional focus area")
    category: Optional[str] = Field(default="Entertainment", description="Question category")


class QuestionGenerationResponse(BaseModel):
    """Model for question generation responses."""
    
    questions: List[Any] = Field(..., description="Generated questions")
    success: bool = Field(default=True, description="Whether generation was successful")
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Generation metadata")
    
    @validator('questions')
    def validate_questions(cls, v):
        """Validate generated questions."""
        valid_questions = []
        for question in v:
            if isinstance(question, dict):
                q_type = question.get('type', 'multiple_choice')
                try:
                    if q_type == 'multiple_choice':
                        valid_questions.append(MultipleChoiceQuestion(**question))
                    elif q_type == 'true_false':
                        valid_questions.append(TrueFalseQuestion(**question))
                    elif q_type == 'open_ended':
                        valid_questions.append(OpenEndedQuestion(**question))
                    else:
                        raise ValueError(f"Unknown question type: {q_type}")
                except Exception as e:
                    raise ValueError(f"Invalid question: {e}")
            elif isinstance(question, (MultipleChoiceQuestion, TrueFalseQuestion, OpenEndedQuestion)):
                valid_questions.append(question)
            else:
                raise ValueError(f"Invalid question format: {type(question)}")
        
        return valid_questions


# Helper functions for creating questions
def create_multiple_choice_question(
    question: str,
    options: List[str],
    correct_letter: str,
    category: str = "Entertainment",
    difficulty: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> MultipleChoiceQuestion:
    """Helper function to create a multiple choice question."""
    
    # Calculate correct answer from letter and options
    correct_index = ord(correct_letter.upper()) - ord('A')
    if correct_index < 0 or correct_index >= len(options):
        raise ValueError(f"correct_letter '{correct_letter}' is out of range for {len(options)} options")
    
    correct_answer = options[correct_index]
    
    return MultipleChoiceQuestion(
        question=question,
        options=options,
        correct_answer=correct_answer,
        correct_letter=correct_letter.upper(),
        category=category,
        difficulty=difficulty,
        metadata=metadata or {}
    )


def create_true_false_question(
    question: str,
    correct_answer: bool,
    category: str = "Entertainment",
    difficulty: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> TrueFalseQuestion:
    """Helper function to create a true/false question."""
    
    return TrueFalseQuestion(
        question=question,
        correct_answer="true" if correct_answer else "false",
        category=category,
        difficulty=difficulty,
        metadata=metadata or {}
    )


def create_open_ended_question(
    question: str,
    correct_answer: str,
    acceptable_answers: Optional[List[str]] = None,
    category: str = "Entertainment", 
    difficulty: str = "medium",
    metadata: Optional[Dict[str, Any]] = None
) -> OpenEndedQuestion:
    """Helper function to create an open-ended question."""
    
    return OpenEndedQuestion(
        question=question,
        correct_answer=correct_answer,
        acceptable_answers=acceptable_answers or [],
        category=category,
        difficulty=difficulty,
        metadata=metadata or {}
    )