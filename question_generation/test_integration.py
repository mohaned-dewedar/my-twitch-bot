#!/usr/bin/env python3
"""
Test script for question generation system integration.

Tests loading data, generating placeholder questions, and formatting
for compatibility with existing database loading scripts.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from question_generation.smite_generator import SmiteQuestionGenerator
from question_generation.utils import validate_question_format, save_questions_json


def test_data_loading():
    """Test loading Smite data."""
    print("=== Testing Data Loading ===")
    
    generator = SmiteQuestionGenerator()
    
    # Test data loading
    success = generator.load_data()
    if not success:
        print("❌ Failed to load data")
        return False
        
    print("✅ Data loaded successfully")
    
    # Test prompts loading
    success = generator.load_prompts()
    if not success:
        print("❌ Failed to load prompts")
        return False
        
    print("✅ Prompts loaded successfully")
    
    # Show statistics
    stats = generator.get_statistics()
    print(f"📊 Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    for doc_type, count in stats['types'].items():
        print(f"   {doc_type}: {count}")
        
    return True


def test_question_generation():
    """Test generating questions for different document types."""
    print("\n=== Testing Question Generation ===")
    
    generator = SmiteQuestionGenerator()
    generator.load_data()
    generator.load_prompts()
    
    available_types = generator.get_available_types()
    print(f"Available document types: {available_types}")
    
    test_results = {}
    
    # Test each document type
    for doc_type in available_types[:3]:  # Test first 3 types
        print(f"\n--- Testing {doc_type} questions ---")
        
        questions = generator.generate_questions(
            document_type=doc_type,
            count=2,  # Generate 2 questions
            question_types=["multiple_choice", "true_false"]
        )
        
        test_results[doc_type] = len(questions)
        print(f"Generated {len(questions)} questions for {doc_type}")
        
        # Validate each question
        for i, q in enumerate(questions):
            is_valid, errors = validate_question_format(q)
            if is_valid:
                print(f"  ✅ Question {i+1}: Valid")
            else:
                print(f"  ❌ Question {i+1}: Invalid - {errors}")
                
    return test_results


def test_database_format_compatibility():
    """Test compatibility with database loading format."""
    print("\n=== Testing Database Format Compatibility ===")
    
    generator = SmiteQuestionGenerator()
    generator.load_data()
    generator.load_prompts()
    
    # Generate some test questions
    questions = generator.generate_questions(
        document_type="god",
        count=3,
        question_types=["multiple_choice"]
    )
    
    if not questions:
        print("❌ No questions generated for testing")
        return False
    
    # Test formatting for database
    formatted = generator.format_for_database(questions, "test_smite_generated")
    
    required_fields = ["bank_name", "source_type", "description", "questions"]
    for field in required_fields:
        if field not in formatted:
            print(f"❌ Missing required field in formatted output: {field}")
            return False
    
    print("✅ Database format structure valid")
    
    # Test individual question format
    for i, q in enumerate(formatted["questions"]):
        required_q_fields = ["question_text", "correct_answer", "question_type"]
        for field in required_q_fields:
            if field not in q:
                print(f"❌ Question {i+1} missing field: {field}")
                return False
    
    print(f"✅ All {len(questions)} questions have required fields")
    
    # Test saving to JSON
    output_file = "/tmp/test_smite_questions.json"
    success = save_questions_json(questions, output_file, "test_smite_generated", "smite")
    
    if success and os.path.exists(output_file):
        print("✅ Successfully saved questions to JSON")
        
        # Verify JSON can be loaded
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        print(f"✅ JSON file valid, contains {len(loaded_data.get('questions', []))} questions")
        
        # Clean up
        os.remove(output_file)
        
    else:
        print("❌ Failed to save questions to JSON")
        return False
    
    return True


def test_prompt_system():
    """Test the prompt generation system."""
    print("\n=== Testing Prompt System ===")
    
    from question_generation.prompts import SmitePrompts
    
    # Test getting available types
    available_types = SmitePrompts.get_available_types()
    print(f"Available prompt types: {available_types}")
    
    available_question_types = SmitePrompts.get_available_question_types()
    print(f"Available question types: {available_question_types}")
    
    # Test prompt generation
    try:
        prompt = SmitePrompts.get_prompt(
            document_type="god",
            question_type="multiple_choice",
            question_count=3,
            difficulty="medium"
        )
        
        print("✅ Prompt generated successfully")
        print(f"   Prompt length: {len(prompt)} characters")
        
        # Check for key elements
        if "{content}" in prompt:
            print("✅ Prompt contains content placeholder")
        else:
            print("❌ Prompt missing content placeholder")
            
    except Exception as e:
        print(f"❌ Error generating prompt: {e}")
        return False
        
    return True


def main():
    """Run all integration tests."""
    print("🧪 Running Question Generation Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Question Generation", test_question_generation), 
        ("Database Format Compatibility", test_database_format_compatibility),
        ("Prompt System", test_prompt_system)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System ready for LLM integration.")
    else:
        print("⚠️  Some tests failed. Please review and fix issues before proceeding.")


if __name__ == "__main__":
    main()