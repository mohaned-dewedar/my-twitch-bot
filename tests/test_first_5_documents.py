#!/usr/bin/env python3
"""
Test script to generate questions for the first 5 documents from all_documents.json
using the question generation system with LLM integration.
"""

import json
from pathlib import Path
from question_generation.smite_generator import SmiteQuestionGenerator
from llm.client import LLMClient
from llm.config import get_question_generation_config


def load_first_5_documents():
    """Load the first 5 documents from all_documents.json."""
    data_file = Path("data/smite/all_documents.json")
    
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        all_documents = json.load(f)
    
    # Get first 5 documents
    first_5 = all_documents[:5]
    
    print(f"📊 Loaded first 5 documents from {len(all_documents)} total documents")
    print("Document types in first 5:")
    for i, doc in enumerate(first_5, 1):
        print(f"  {i}. {doc['type']}: {doc['name']}")
    
    return first_5


def test_question_generation():
    """Test question generation for first 5 documents."""
    print("🧪 Testing Question Generation with First 5 Documents")
    print("=" * 60)
    
    # Load documents
    try:
        documents = load_first_5_documents()
    except FileNotFoundError as e:
        print(f"❌ Error loading documents: {e}")
        return
    
    # Check LLM service
    config = get_question_generation_config()
    print(f"\n🤖 Using LLM config: {config}")
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ LLM service not available")
            print("   Make sure Ollama is running: ollama serve")
            print("   And granite3.2:8b is installed: ollama pull granite3.2:8b")
            return
        
        print("✅ LLM service is healthy")
        
        # Initialize question generator
        generator = SmiteQuestionGenerator(llm_client=client)
        
        # Process each document
        for i, document in enumerate(documents, 1):
            print(f"\n{'='*50}")
            print(f"📝 Document {i}: {document['type']} - {document['name']}")
            print(f"{'='*50}")
            
            try:
                # Generate questions for this document
                questions = generator.generate_questions_for_document(document)
                
                if questions:
                    print(f"✅ Generated {len(questions)} question(s):")
                    
                    for j, question in enumerate(questions, 1):
                        print(f"\n🔸 Question {j}:")
                        print(f"   Q: {question.get('question', 'N/A')}")
                        
                        # Display answer choices if available
                        if question.get('type') == 'multiple_choice' and question.get('options'):
                            options = question['options']
                            correct = question.get('correct_answer', '')
                            correct_letter = question.get('correct_letter', '')
                            
                            print("   Options:")
                            for k, option in enumerate(options):
                                marker = "✓" if option == correct else " "
                                print(f"     {chr(65+k)}. {marker} {option}")
                            
                            if correct_letter:
                                print(f"   Correct Letter: {correct_letter}")
                        
                        print(f"   Type: {question.get('type', 'N/A')}")
                        print(f"   Difficulty: {question.get('difficulty', 'N/A')}")
                        print(f"   Category: {question.get('category', 'N/A')}")
                else:
                    print("❌ No questions generated")
                    
            except Exception as e:
                print(f"❌ Error generating questions for {document['name']}: {e}")
                continue
    
    print(f"\n{'='*60}")
    print("🎯 Test completed!")


def main():
    """Run the test."""
    try:
        test_question_generation()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise


if __name__ == "__main__":
    main()