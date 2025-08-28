import json
from difflib import get_close_matches
from typing import Optional, Dict, List


class SmiteDataStore:
    """Handles loading and querying Smite gods and abilities data."""
    
    def __init__(self, data_file_path: str = "data/smite_gods_modified.json"):
        self.data_file_path = data_file_path
        self.gods_data = []
        self.ability_to_god = {}
        self.god_to_abilities = {}

    def load_data(self) -> bool:
        """Load Smite data from JSON file and build lookup tables."""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.gods_data = data.get('gods', [])

            for god in self.gods_data:
                god_name = god['name']
                abilities = god.get('abilities', [])
                self.god_to_abilities[god_name] = abilities
                for ability in abilities:
                    self.ability_to_god[ability] = god_name

            print(f"Loaded {len(self.gods_data)} gods with {len(self.ability_to_god)} abilities")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to load Smite data: {e}")
            return False

    def get_all_gods(self) -> List[str]:
        """Get list of all god names."""
        return list(self.god_to_abilities.keys())

    def get_all_abilities(self) -> List[str]:
        """Get list of all ability names."""
        return list(self.ability_to_god.keys())

    def get_god_by_ability(self, ability: str) -> Optional[str]:
        """Get the god who owns a specific ability."""
        return self.ability_to_god.get(ability)

    def get_abilities_by_god(self, god_name: str) -> List[str]:
        """Get all abilities for a specific god."""
        return self.god_to_abilities.get(god_name, [])

    def search_god(self, query: str) -> Optional[Dict]:
        """Search for a god by name (partial match)."""
        query = query.lower().strip()
        for god in self.gods_data:
            if query in god['name'].lower():
                return god
        return None

    def search_ability(self, query: str) -> Optional[str]:
        """Search for an ability by name (partial match)."""
        query = query.lower().strip()
        for ability in self.ability_to_god.keys():
            if query in ability.lower():
                return ability
        return None

    def fuzzy_match_god(self, user_input: str) -> Optional[str]:
        """Find closest matching god name using fuzzy matching."""
        user_input = user_input.lower().strip()
        all_gods = self.get_all_gods()
        matches = get_close_matches(user_input, [g.lower() for g in all_gods], n=1, cutoff=0.7)
        if matches:
            for god in all_gods:
                if god.lower() == matches[0]:
                    return god
        return None