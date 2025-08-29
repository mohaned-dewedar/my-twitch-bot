#!/usr/bin/env python3
"""
Test Empty Response Handling

Test that the LLM can appropriately decide to skip documents that aren't 
suitable for trivia questions by returning empty JSON arrays.
"""

from question_generation.smite_generator import SmiteQuestionGenerator
from llm.client import LLMClient
from llm.config import get_question_generation_config


def test_empty_response_handling():
    """Test that the system handles empty responses correctly."""
    print("🧪 Testing Empty Response Handling")
    print("=" * 50)
    
    # Create mock documents with varying trivia potential
    test_documents = [
        {
            "id": "test_good",
            "type": "god",
            "name": "Test Good Trivia",
            "content": "Thor is a Norse god with 480 health, 205 mana, and has abilities like Mjolnir's Attunement (passive) and Anvil of Dawn (ultimate). His base physical protection is 18."
        },
        {
            "id": "test_vague",
            "type": "ability", 
            "name": "Test Vague Content",
            "content": "This ability does something. It has some effect. Players can use it in certain situations."
        },
        {
            "id": "test_technical",
            "type": "patch",
            "name": "Test Technical",
            "content": "Updated rendering pipeline for improved frame rate optimization. Refactored internal data structures for better memory management."
        },
        {
            "id": "test_specific",
            "type": "item",
            "name": "Test Specific Item",
            "content": "Heartseeker costs 2300 gold and provides +65 Physical Power and +10 Physical Penetration. Passive: Your abilities deal an additional 3% of the target's current Health as Physical Damage."
        }
    ]
    
    # Initialize LLM client
    config = get_question_generation_config()
    with LLMClient(config) as client:
        if not client.health_check():
            print("❌ LLM service not available")
            return
        
        print("✅ LLM service is healthy")
        
        # Initialize generator
        generator = SmiteQuestionGenerator(llm_client=client)
        
        results = {}
        
        # Test each document
        for doc in test_documents:
            print(f"\n📝 Testing document: {doc['name']}")
            print(f"Content: {doc['content'][:80]}...")
            
            try:
                questions = generator.generate_questions_for_document(doc)
                
                if questions:
                    print(f"✅ Generated {len(questions)} questions")
                    results[doc['name']] = 'generated'
                    
                    # Show first question as example
                    if questions:
                        q = questions[0]
                        print(f"   Example Q: {q.get('question', 'N/A')}")
                else:
                    print(f"📝 LLM decided to skip (returned empty)")
                    results[doc['name']] = 'skipped'
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                results[doc['name']] = 'error'
        
        # Summary
        print(f"\n📊 Test Results Summary")
        print("=" * 30)
        for doc_name, result in results.items():
            emoji = {"generated": "✅", "skipped": "📝", "error": "❌"}[result]
            print(f"{emoji} {doc_name}: {result}")
        
        # Analyze results
        generated_count = sum(1 for r in results.values() if r == 'generated')
        skipped_count = sum(1 for r in results.values() if r == 'skipped')
        
        print(f"\n🎯 Analysis:")
        print(f"Generated questions: {generated_count}/{len(test_documents)}")
        print(f"Skipped documents: {skipped_count}/{len(test_documents)}")
        
        if skipped_count > 0:
            print("✅ Empty response handling is working - LLM can skip unsuitable content")
        else:
            print("⚠️  LLM generated questions for all documents - may need to adjust prompts")


if __name__ == "__main__":
    test_empty_response_handling()