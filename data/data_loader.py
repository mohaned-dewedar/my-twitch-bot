import json
import random
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

class SmiteDataLoader:
    def __init__(self, data_file_path: str = "data/smite_gods_modified.json"):
        """
        Initialize the Smite data loader with the path to the JSON file.
        
        Args:
            data_file_path: Path to the JSON file containing smite gods data
        """
        self.data_file_path = data_file_path
        self.gods_data = []
        self.ability_to_god = {}
        self.god_to_abilities = {}
        self.current_trivia = None
        self.trivia_active = False
        self.correct_answer = None
    def check_smite_answer(self, user_answer: str, username: str) -> str:
        is_correct, correct = self.data_loader.check_trivia_answer(user_answer)
        if is_correct:
            self.data_loader.end_trivia()
            return f"🎉 @{username} got it right! The answer was: {correct}"
        else:
            return f"❌ @{username} - That’s not correct. Try again!"
    def load_data(self) -> bool:
        """
        Load the smite gods data from the JSON file and build the ability-to-god mapping.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.gods_data = data.get('gods', [])
                
            # Build ability-to-god mapping
            for god in self.gods_data:
                god_name = god['name']
                abilities = god.get('abilities', [])
                
                # Store god's abilities
                self.god_to_abilities[god_name] = abilities
                
                # Map each ability to the god
                for ability in abilities:
                    self.ability_to_god[ability] = god_name
                    
            print(f"Loaded {len(self.gods_data)} gods with {len(self.ability_to_god)} abilities")
            return True
            
        except FileNotFoundError:
            print(f"Error: Could not find data file at {self.data_file_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in data file: {e}")
            return False
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def get_random_ability(self) -> Optional[str]:
        """
        Get a random ability from the loaded data.
        
        Returns:
            str: Random ability name or None if no data loaded
        """
        if not self.ability_to_god:
            return None
        return random.choice(list(self.ability_to_god.keys()))
    
    def get_god_by_ability(self, ability: str) -> Optional[str]:
        """
        Get the god name that owns a specific ability.
        
        Args:
            ability: The ability name to look up
            
        Returns:
            str: God name that owns the ability, or None if not found
        """
        return self.ability_to_god.get(ability)
    
    def get_abilities_by_god(self, god_name: str) -> List[str]:
        """
        Get all abilities for a specific god.
        
        Args:
            god_name: The name of the god
            
        Returns:
            List[str]: List of ability names for the god
        """
        return self.god_to_abilities.get(god_name, [])
    
    def start_trivia(self) -> Optional[str]:
        """
        Start a new trivia game by selecting a random ability.
        
        Returns:
            str: The ability name for the trivia, or None if no data loaded
        """
        if not self.ability_to_god:
            return None
            
        ability = self.get_random_ability()
        if ability:
            self.current_trivia = ability
            self.correct_answer = self.ability_to_god[ability]
            self.trivia_active = True
            return ability
        return None
    
    def check_trivia_answer(self, user_answer: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a user's answer to the current trivia is correct.
        
        Args:
            user_answer: The user's answer (god name)
            
        Returns:
            Tuple[bool, Optional[str]]: (is_correct, correct_answer)
        """
        if not self.trivia_active or not self.correct_answer:
            return False, None
            
        # Case-insensitive comparison
        is_correct = user_answer.lower().strip() == self.correct_answer.lower().strip()
        return is_correct, self.correct_answer
    
    def start_smite_trivia(self) -> Optional[dict]:
        """
        Start a new smite trivia question.
        Returns the question dict or None if failed.
        """
        if self.data_loader.is_trivia_active():
            return self.data_loader.get_current_question()
        
        ability = self.data_loader.start_trivia()
        if ability:
            return self.data_loader.get_current_question()
        return None
    def end_trivia(self):
        """End the current trivia game."""
        self.trivia_active = False
        self.current_trivia = None
        self.correct_answer = None
    
    def get_current_trivia(self) -> Optional[str]:
        """
        Get the current trivia ability.
        
        Returns:
            str: Current trivia ability or None if no active trivia
        """
        return self.current_trivia
    def get_current_question(self) -> Optional[dict]:
        """
        Return a structured trivia question if one is active.
        """
        if self.trivia_active and self.current_trivia and self.correct_answer:
            return {
                "question": f"Which god has the ability: {self.current_trivia}?",
                "correct_answer": self.correct_answer,
                "ability": self.current_trivia,
                "category": "Smite"
            }
        return None  
    def fuzzy_match_god(self, user_input: str) -> Optional[str]:
        """
        Try to fuzzy match user input to known god names.
        
        Returns:
            str: Matched god name or None if not found
        """
        user_input = user_input.lower().strip()
        all_gods = self.get_all_gods()

        # Case-insensitive close match
        matches = get_close_matches(user_input, [g.lower() for g in all_gods], n=1, cutoff=0.7)
        if matches:
            # Get original cased name
            for god in all_gods:
                if god.lower() == matches[0]:
                    return god
        return None

    def is_trivia_active(self) -> bool:
        """
        Check if a trivia game is currently active.
        
        Returns:
            bool: True if trivia is active, False otherwise
        """
        return self.trivia_active
    
    def get_all_gods(self) -> List[str]:
        """
        Get a list of all god names.
        
        Returns:
            List[str]: List of all god names
        """
        return [god['name'] for god in self.gods_data]
    
    def get_all_abilities(self) -> List[str]:
        """
        Get a list of all ability names.
        
        Returns:
            List[str]: List of all ability names
        """
        return list(self.ability_to_god.keys())
    
    def search_god(self, query: str) -> Optional[Dict]:
        """
        Search for a god by name (case-insensitive partial match).
        
        Args:
            query: The search query
            
        Returns:
            Dict: God data if found, None otherwise
        """
        query_lower = query.lower().strip()
        for god in self.gods_data:
            if query_lower in god['name'].lower():
                return god
        return None
    
    def search_ability(self, query: str) -> Optional[str]:
        """
        Search for an ability by name (case-insensitive partial match).
        
        Args:
            query: The search query
            
        Returns:
            str: Ability name if found, None otherwise
        """
        query_lower = query.lower().strip()
        for ability in self.ability_to_god.keys():
            if query_lower in ability.lower():
                return ability
        return None 