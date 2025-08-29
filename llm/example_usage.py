#!/usr/bin/env python3
"""
Example Usage of LLM Client

Demonstrates how to use the LLMClient for various tasks including
question generation integration.
"""

import json
from llm import LLMClient, LLMConfig


def basic_text_generation():
    """Example of basic text generation."""
    print("=== Basic Text Generation ===")
    
    config = LLMConfig(
        host="http://localhost:11434",
        model="granite3.2:8b",
        temperature=0.7
    )
    
    with LLMClient(config) as client:
        # Check if service is available
        if not client.health_check():
            print("❌ LLM service not available")
            return
            
        print("✅ LLM service is healthy")
        
        # Simple text generation
        prompt = "Write a short explanation of what a trivia question is."
        response = client.generate(prompt)
        
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")


def json_generation_example():
    """Example of JSON generation for structured data."""
    print("\n=== JSON Generation Example ===")
    
    config = LLMConfig(
        host="http://localhost:11434",
        model="granite3.2:8b",
        temperature=0.3  # Lower temperature for more consistent JSON
    )
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ LLM service not available")
            return
            
        # Generate structured JSON response
        prompt = """
        Create a sample multiple choice trivia question about science.
        Format as JSON with these fields:
        - question: the question text
        - options: array of 4 answer choices
        - correct_answer: the correct answer from the options
        - type: "multiple_choice"
        - category: "Science"
        - difficulty: "medium"
        """
        
        try:
            json_response = client.generate_json(prompt)
            print("Generated JSON question:")
            print(json.dumps(json_response, indent=2))
            
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")


def question_generation_integration():
    """Example integration with question generation system."""
    print("\n=== Question Generation Integration ===")
    
    # Simulate Smite god data
    sample_god_data = {
        "name": "Thor",
        "type": "god",
        "content": """Thor is a powerful Norse god in Smite known for his lightning abilities. 
        His health is 480 (+85 per level) and mana is 205 (+38 per level). 
        His passive ability is Warrior's Madness which increases his physical power. 
        His ultimate ability is Anvil of Dawn which deals massive damage."""
    }
    
    # Create prompt for question generation
    prompt = f"""
    Create 2 multiple choice trivia questions about this Smite god:
    
    God Data: {sample_god_data['content']}
    
    Focus on:
    - God stats (health, mana, abilities)
    - Pantheon and lore
    - Specific ability names
    
    Format as JSON array with each question having:
    - question: the question text  
    - options: array of 4 choices
    - correct_answer: correct choice from options
    - type: "multiple_choice"
    - category: "Entertainment"
    - difficulty: "medium"
    """
    
    config = LLMConfig(
        host="http://localhost:11434",
        model="granite3.2:8b", 
        temperature=0.4,
        num_predict=800
    )
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ LLM service not available")
            return
            
        try:
            questions = client.generate_json(prompt)
            
            if isinstance(questions, list):
                print(f"✅ Generated {len(questions)} questions:")
                for i, q in enumerate(questions, 1):
                    print(f"\nQuestion {i}: {q.get('question', 'N/A')}")
                    for j, option in enumerate(q.get('options', [])):
                        marker = "✓" if option == q.get('correct_answer') else " "
                        print(f"   {chr(65+j)}. {marker} {option}")
            else:
                print("✅ Generated single question:")
                print(json.dumps(questions, indent=2))
                
        except Exception as e:
            print(f"❌ Question generation failed: {e}")


def model_listing_example():
    """Example of listing available models."""
    print("\n=== Available Models ===")
    
    config = LLMConfig(host="http://localhost:11434")
    
    with LLMClient(config) as client:
        if client.health_check():
            models = client.get_models()
            print(f"Available models: {models}")
        else:
            print("❌ LLM service not available")


def main():
    """Run all examples."""
    print("🤖 LLM Client Examples")
    print("=" * 50)
    
    examples = [
        ("Basic Text Generation", basic_text_generation),
        ("JSON Generation", json_generation_example),
        ("Question Generation Integration", question_generation_integration),
        ("Model Listing", model_listing_example)
    ]
    
    for example_name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ Example '{example_name}' failed: {e}")
            
    print("\n🎯 Examples completed!")
    print("\nNext steps:")
    print("1. Start Ollama service: ollama serve")
    print("2. Pull a model: ollama pull llama3.2")
    print("3. Update question generation to use LLMClient")


if __name__ == "__main__":
    main()