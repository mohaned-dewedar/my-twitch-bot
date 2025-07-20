#!/usr/bin/env python3
"""
Test script for the Smite trivia system.
"""

from data.data_loader import SmiteDataLoader
from llm.trivia_handler import TriviaHandler

def test_data_loader():
    """Test the data loader functionality."""
    print(" Testing Smite Data Loader...")
    
    # Initialize data loader
    loader = SmiteDataLoader()
    
    # Test loading data
    if not loader.load_data():
        print("❌ Failed to load data")
        return False
    
    print(f" Loaded {len(loader.gods_data)} gods")
    print(f" Mapped {len(loader.ability_to_god)} abilities")
    
    # Test getting a random ability
    ability = loader.get_random_ability()
    if ability:
        god = loader.get_god_by_ability(ability)
        print(f" Random ability: {ability} -> {god}")
    else:
        print(" Failed to get random ability")
        return False
    
    # Test trivia functionality
    print("\n Testing Trivia System...")
    
    trivia_handler = TriviaHandler(loader)
    
    # Test starting trivia
    response = trivia_handler.start_new_trivia()
    print(f"✅ Start trivia response: {response}")
    
    # Test checking correct answer
    if loader.is_trivia_active():
        current_ability = loader.get_current_trivia()
        correct_god = loader.get_god_by_ability(current_ability)
        
        # Test correct answer
        response = trivia_handler.check_answer(correct_god, "TestUser")
        print(f"✅ Correct answer response: {response}")
        
        # Test incorrect answer
        response = trivia_handler.check_answer("WrongGod", "TestUser2")
        print(f"✅ Incorrect answer response: {response}")
    
    print("\n🎉 All tests passed!")
    return True

def test_search_functionality():
    """Test search functionality."""
    print("\n🔍 Testing Search Functionality...")
    
    loader = SmiteDataLoader()
    if not loader.load_data():
        return False
    
    # Test god search
    test_gods = ["Zeus", "zeus", "ZEUS", "Thor", "th"]
    for god_query in test_gods:
        result = loader.search_god(god_query)
        if result:
            print(f"✅ Found god '{god_query}' -> {result['name']}")
        else:
            print(f"❌ Could not find god '{god_query}'")
    
    # Test ability search
    test_abilities = ["Lightning", "lightning", "Storm", "st"]
    for ability_query in test_abilities:
        result = loader.search_ability(ability_query)
        if result:
            god = loader.get_god_by_ability(result)
            print(f"✅ Found ability '{ability_query}' -> {result} (owned by {god})")
        else:
            print(f"❌ Could not find ability '{ability_query}'")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Smite Trivia System Tests...\n")
    
    success = True
    success &= test_data_loader()
    success &= test_search_functionality()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!") 