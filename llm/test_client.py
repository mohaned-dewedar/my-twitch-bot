#!/usr/bin/env python3
"""
Test script for LLM client functionality.

Tests basic operations and validates the client works correctly
with different configurations.
"""

import json
from llm import LLMClient, LLMConfig
from llm.config import LLMPresets, get_question_generation_config


def test_connection():
    """Test basic connection to LLM service."""
    print("=== Testing Connection ===")
    
    config = LLMPresets.ollama_local("granite3.2:8b")
    
    with LLMClient(config) as client:
        is_healthy = client.health_check()
        
        if is_healthy:
            print("✅ LLM service is available")
            
            # Get available models
            models = client.get_models()
            print(f"📋 Available models: {models}")
            
            return True
        else:
            print("❌ LLM service not available")
            print("   Make sure Ollama is running: ollama serve")
            print("   And you have a model installed: ollama pull llama3.2")
            return False


def test_simple_generation():
    """Test simple text generation."""
    print("\n=== Testing Simple Generation ===")
    
    config = LLMPresets.ollama_precise("granite3.2:8b")
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ Skipping - service unavailable")
            return False
            
        try:
            prompt = "What is 2 + 2?"
            response = client.generate(prompt, num_predict=50)
            
            print(f"Prompt: {prompt}")
            print(f"Response: {response}")
            
            if response and len(response) > 0:
                print("✅ Simple generation works")
                return True
            else:
                print("❌ Empty response")
                return False
                
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return False


def test_json_generation():
    """Test JSON generation and parsing."""
    print("\n=== Testing JSON Generation ===")
    
    config = LLMPresets.ollama_precise("granite3.2:8b")
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ Skipping - service unavailable")
            return False
            
        try:
            prompt = """
            Create a simple JSON object with these fields:
            - name: "Test Question"
            - type: "test"
            - count: 1
            """
            
            json_response = client.generate_json(prompt, num_predict=100)
            
            print(f"JSON Response: {json.dumps(json_response, indent=2)}")
            
            # Validate structure
            required_fields = ["name", "type", "count"]
            if all(field in json_response for field in required_fields):
                print("✅ JSON generation and parsing works")
                return True
            else:
                print(f"❌ Missing fields in JSON response: {required_fields}")
                return False
                
        except Exception as e:
            print(f"❌ JSON generation failed: {e}")
            return False


def test_question_generation_config():
    """Test the question generation configuration."""
    print("\n=== Testing Question Generation Config ===")
    
    config = get_question_generation_config()
    print(f"Question generation config: {config}")
    
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ Skipping - service unavailable")
            return False
            
        try:
            # Test with a trivia-style prompt
            prompt = """
            Generate 1 multiple choice trivia question about mathematics.
            
            Format as JSON:
            {
                "question": "question text",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "correct option",
                "type": "multiple_choice",
                "difficulty": "easy"
            }
            """
            
            question = client.generate_json(prompt, num_predict=300)
            
            print("Generated question:")
            print(json.dumps(question, indent=2))
            
            # Basic validation
            required_fields = ["question", "options", "correct_answer", "type"]
            if all(field in question for field in required_fields):
                print("✅ Question generation config works")
                return True
            else:
                print("❌ Generated question missing required fields")
                return False
                
        except Exception as e:
            print(f"❌ Question generation test failed: {e}")
            return False


def test_error_handling():
    """Test error handling with bad requests."""
    print("\n=== Testing Error Handling ===")
    
    # Test with non-existent service
    bad_config = LLMConfig(
        host="http://localhost:9999",  # Non-existent port
    )
    
    with LLMClient(bad_config) as client:
        try:
            response = client.generate("Hello")
            print(f"❌ Expected error but got response: {response}")
            return False
            
        except Exception as e:
            print(f"✅ Error handling works: {e}")
            return True


def main():
    """Run all tests."""
    print("🧪 Testing LLM Client")
    print("=" * 50)
    
    tests = [
        ("Connection Test", test_connection),
        ("Simple Generation", test_simple_generation),
        ("JSON Generation", test_json_generation),
        ("Question Config", test_question_generation_config),
        ("Error Handling", test_error_handling)
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
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! LLM client ready for use.")
    else:
        print("⚠️  Some tests failed. Check LLM service availability.")
        
    print("\nSetup instructions:")
    print("1. Install Ollama: https://ollama.ai/")
    print("2. Start service: ollama serve")
    print("3. Pull model: ollama pull llama3.2")


if __name__ == "__main__":
    main()