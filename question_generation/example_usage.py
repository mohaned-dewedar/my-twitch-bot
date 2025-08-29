#!/usr/bin/env python3
"""
Example Usage of Question Generation System

Demonstrates how to use the SmiteQuestionGenerator to create
trivia questions from Smite data.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from question_generation import SmiteQuestionGenerator
from question_generation.utils import save_questions_json


def main():
    """Example usage of the question generation system."""
    
    print("🎯 Smite Question Generation Example")
    print("=" * 50)
    
    # Initialize the generator
    generator = SmiteQuestionGenerator()
    
    # Load data and prompts
    print("📥 Loading Smite data...")
    if not generator.load_data():
        print("❌ Failed to load data")
        return
        
    if not generator.load_prompts():
        print("❌ Failed to load prompts")
        return
    
    # Show available data
    stats = generator.get_statistics()
    print(f"✅ Loaded {stats['total_documents']} documents")
    for doc_type, count in stats['types'].items():
        print(f"   {doc_type}: {count}")
    
    # Generate questions for different types
    print("\n🎲 Generating sample questions...")
    
    # Example 1: Generate god questions
    god_questions = generator.generate_questions(
        document_type="god",
        count=3,
        question_types=["multiple_choice", "true_false"],
        difficulty="medium"
    )
    
    print(f"\n--- God Questions ({len(god_questions)}) ---")
    for i, q in enumerate(god_questions, 1):
        print(f"{i}. {q['question']}")
        if q['type'] == 'multiple_choice':
            for j, option in enumerate(q['options']):
                marker = "✓" if option == q['correct_answer'] else " "
                print(f"   {chr(65+j)}. {marker} {option}")
        else:
            print(f"   Answer: {q['correct_answer']}")
        print()
    
    # Example 2: Generate ability questions
    ability_questions = generator.generate_questions(
        document_type="ability", 
        count=2,
        question_types=["open_ended"],
        difficulty="hard"
    )
    
    print(f"--- Ability Questions ({len(ability_questions)}) ---")
    for i, q in enumerate(ability_questions, 1):
        print(f"{i}. {q['question']}")
        print(f"   Answer: {q['correct_answer']}")
        print()
    
    # Example 3: Save questions to file
    all_questions = god_questions + ability_questions
    output_file = "generated_questions/example_output.json"
    
    # Create directory if it doesn't exist
    os.makedirs("generated_questions", exist_ok=True)
    
    success = save_questions_json(
        questions=all_questions,
        output_file=output_file,
        question_bank_name="smite_example_generated",
        source_type="smite"
    )
    
    if success:
        print(f"💾 Saved {len(all_questions)} questions to {output_file}")
        print("   Ready for loading with: uv run python -m scripts.load_questions --sources custom_json")
    else:
        print("❌ Failed to save questions")
    
    # Example 4: Show prompt for LLM integration
    print("\n🤖 Example prompt for LLM integration:")
    print("-" * 40)
    
    # Get a sample document
    gods = generator.get_documents_by_type("god", limit=1)
    if gods:
        from question_generation.prompts import SmitePrompts
        
        sample_prompt = SmitePrompts.get_prompt(
            document_type="god",
            question_type="multiple_choice", 
            question_count=2,
            difficulty="medium"
        )
        
        # Fill in content
        sample_content = gods[0].get('content', '')[:200] + "..."
        filled_prompt = sample_prompt.replace("{content}", sample_content)
        
        print(filled_prompt[:500] + "..." if len(filled_prompt) > 500 else filled_prompt)
    
    print("\n✨ Ready to integrate with LLM!")
    print("Next steps:")
    print("1. Replace placeholder question generation with LLM calls")
    print("2. Add error handling for LLM responses")
    print("3. Implement batch processing for efficiency")
    print("4. Add question quality validation")


if __name__ == "__main__":
    main()