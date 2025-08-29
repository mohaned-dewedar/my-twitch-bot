"""
Utility functions for question generation.

Helper functions for formatting, validation, and data processing
used across different question generators.
"""

import json
import re
import hashlib
from typing import Dict, List, Any, Optional


def clean_text(text: str) -> str:
    """
    Clean text for use in questions.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text suitable for questions
    """
    if not text:
        return ""
        
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    # Fix common formatting issues
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    
    return text


def extract_numbers(text: str) -> List[str]:
    """
    Extract numerical values from text.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of numerical strings found in text
    """
    # Match integers, decimals, percentages
    number_pattern = r'\b\d+(?:\.\d+)?%?\b'
    return re.findall(number_pattern, text)


def generate_question_id(question_text: str, source_id: str = None) -> str:
    """
    Generate a unique ID for a question.
    
    Args:
        question_text: The question text
        source_id: Optional source document ID
        
    Returns:
        Unique question ID
    """
    # Create hash from question text and source
    content = f"{question_text}:{source_id or ''}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]


def validate_question_format(question: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate question format and content.
    
    Args:
        question: Question dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    required_fields = ["question", "correct_answer", "type"]
    for field in required_fields:
        if field not in question:
            errors.append(f"Missing required field: {field}")
        elif not question[field]:
            errors.append(f"Empty required field: {field}")
    
    # Validate question type
    valid_types = ["multiple_choice", "true_false", "open_ended"]
    if "type" in question and question["type"] not in valid_types:
        errors.append(f"Invalid question type: {question['type']}")
    
    # Type-specific validation
    if question.get("type") == "multiple_choice":
        if "options" not in question:
            errors.append("Multiple choice question missing options")
        elif not isinstance(question["options"], list):
            errors.append("Options must be a list")
        elif len(question["options"]) < 2:
            errors.append("Multiple choice needs at least 2 options")
        elif question.get("correct_answer") not in question.get("options", []):
            errors.append("Correct answer not found in options")
    
    elif question.get("type") == "true_false":
        valid_answers = ["true", "false", "True", "False"]
        if question.get("correct_answer") not in valid_answers:
            errors.append("True/false answer must be 'true' or 'false'")
    
    # Check question length
    if len(question.get("question", "")) < 10:
        errors.append("Question text too short")
    elif len(question.get("question", "")) > 500:
        errors.append("Question text too long")
    
    return len(errors) == 0, errors


def create_multiple_choice_distractors(
    correct_answer: str, 
    similar_values: List[str] = None,
    count: int = 3
) -> List[str]:
    """
    Generate plausible incorrect options for multiple choice questions.
    
    Args:
        correct_answer: The correct answer
        similar_values: List of similar values to use as distractors
        count: Number of distractors to generate
        
    Returns:
        List of distractor options
    """
    distractors = []
    
    # Use provided similar values first
    if similar_values:
        distractors.extend([v for v in similar_values if v != correct_answer])
    
    # If we need more distractors, generate them
    if len(distractors) < count:
        # For numerical answers, create variations
        if correct_answer.isdigit():
            base_num = int(correct_answer)
            variations = [
                str(base_num + 1),
                str(base_num - 1),
                str(base_num * 2),
                str(int(base_num * 0.5)) if base_num > 1 else str(base_num + 2)
            ]
            distractors.extend([v for v in variations if v != correct_answer])
        
        # Generic distractors
        generic_options = ["Unknown", "None", "All of the above", "Variable"]
        distractors.extend([opt for opt in generic_options if opt != correct_answer])
    
    # Return unique distractors up to requested count
    unique_distractors = []
    seen = set()
    for d in distractors:
        if d not in seen and d != correct_answer:
            unique_distractors.append(d)
            seen.add(d)
            if len(unique_distractors) >= count:
                break
    
    return unique_distractors


def format_for_trivia_system(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format questions for compatibility with existing trivia system.
    
    Args:
        questions: List of generated questions
        
    Returns:
        List of questions formatted for trivia system
    """
    formatted = []
    
    for q in questions:
        formatted_q = {
            "question": clean_text(q["question"]),
            "correct_answer": q["correct_answer"],
            "type": q.get("type", "multiple_choice"),
            "category": q.get("category", "Entertainment"),
            "difficulty": q.get("difficulty", "medium"),
            "id": generate_question_id(q["question"], q.get("metadata", {}).get("source_document_id"))
        }
        
        # Add options for multiple choice
        if q.get("type") == "multiple_choice" and "options" in q:
            formatted_q["answer_options"] = q["options"]
        
        # Add metadata
        if "metadata" in q:
            formatted_q["source_metadata"] = q["metadata"]
        
        formatted.append(formatted_q)
    
    return formatted


def save_questions_json(
    questions: List[Dict[str, Any]], 
    output_file: str,
    question_bank_name: str,
    source_type: str = "generated"
) -> bool:
    """
    Save questions to JSON file in database-compatible format.
    
    Args:
        questions: List of questions to save
        output_file: Output file path
        question_bank_name: Name for the question bank
        source_type: Type of source data
        
    Returns:
        bool: True if saved successfully
    """
    try:
        output_data = {
            "bank_name": question_bank_name,
            "source_type": source_type,
            "description": f"Auto-generated questions from {source_type} data",
            "question_count": len(questions),
            "questions": format_for_trivia_system(questions)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        return True
        
    except Exception as e:
        print(f"Error saving questions to {output_file}: {e}")
        return False


def load_questions_json(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load questions from JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of questions or None if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "questions" in data:
            return data["questions"]
        else:
            print(f"Unexpected JSON structure in {file_path}")
            return None
            
    except Exception as e:
        print(f"Error loading questions from {file_path}: {e}")
        return None


def get_category_for_smite_type(document_type: str) -> str:
    """
    Map Smite document types to trivia categories.
    
    Args:
        document_type: Smite document type
        
    Returns:
        Appropriate trivia category
    """
    category_mapping = {
        "god": "Entertainment",
        "ability": "Entertainment", 
        "patch": "Entertainment",
        "god_change": "Entertainment",
        "item": "Entertainment"
    }
    
    return category_mapping.get(document_type, "General")