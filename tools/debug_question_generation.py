#!/usr/bin/env python3
"""
Debug script to see what questions are being generated and why validation fails.
"""

import json
from pathlib import Path
from question_generation.smite_generator import SmiteQuestionGenerator
from question_generation.prompts import SmitePrompts
from llm.client import LLMClient
from llm.config import get_question_generation_config


def debug_single_document():
    """Debug question generation for a single document."""
    print("🔍 Debugging Question Generation")
    print("=" * 50)
    
    # Load first document
    data_file = Path("data/smite/all_documents.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        all_documents = json.load(f)
    
    first_doc = all_documents[0]  # Achilles (god type)
    print(f"📋 Testing with: {first_doc['type']} - {first_doc['name']}")
    print(f"Content preview: {first_doc['content'][:200]}...")
    
    # Get the prompt that will be used
    prompt_template = SmitePrompts.get_prompt(
        document_type=first_doc['type'],
        question_type='multiple_choice',
        question_count=1,
        difficulty='medium'
    )
    
    prompt = prompt_template.replace("{content}", first_doc['content'])
    print(f"\n📝 Generated Prompt:")
    print("-" * 30)
    print(prompt)
    print("-" * 30)
    
    # Test LLM response directly
    config = get_question_generation_config()
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ LLM service not available")
            return
            
        print("✅ LLM service healthy")
        
        try:
            # Get raw LLM response
            print("\n🤖 Raw LLM Response:")
            print("-" * 30)
            raw_response = client.generate(prompt)
            print(raw_response)
            print("-" * 30)
            
            # Try JSON parsing
            print("\n🔧 JSON Parsing Attempt:")
            json_response = client.generate_json(prompt)
            print(f"Type: {type(json_response)}")
            print(f"Content: {json.dumps(json_response, indent=2)}")
            
            # Test validation
            print("\n✅ Validation Test:")
            generator = SmiteQuestionGenerator()
            
            if isinstance(json_response, list):
                for i, question in enumerate(json_response):
                    is_valid = generator.validate_question(question)
                    print(f"Question {i+1}: {'✅ Valid' if is_valid else '❌ Invalid'}")
                    if not is_valid:
                        print(f"   Content: {json.dumps(question, indent=4)}")
            elif isinstance(json_response, dict):
                is_valid = generator.validate_question(json_response)
                print(f"Single question: {'✅ Valid' if is_valid else '❌ Invalid'}")
                if not is_valid:
                    print(f"   Content: {json.dumps(json_response, indent=4)}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    debug_single_document()