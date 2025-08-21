"""
Category mapping for OpenTDB trivia categories.
Groups related categories into broader, cleaner categories.
"""

# Main category groupings
CATEGORY_GROUPS = {
    "Entertainment": [
        "Entertainment: Books",
        "Entertainment: Film", 
        "Entertainment: Music",
        "Entertainment: Musicals & Theatres",
        "Entertainment: Television",
        "Entertainment: Video Games",
        "Entertainment: Board Games",
        "Entertainment: Comics",
        "Entertainment: Japanese Anime & Manga",
        "Entertainment: Cartoon & Animations"
    ],
    "Science": [
        "Science & Nature",
        "Science: Computers", 
        "Science: Mathematics",
        "Science: Gadgets"
    ],
    "Culture": [
        "History",
        "Geography", 
        "Mythology",
        "Art",
        "Politics"
    ],
    "General": [
        "General Knowledge",
        "Sports",
        "Animals",
        "Vehicles", 
        "Celebrities"
    ]
}

# Reverse mapping: specific category -> main category
CATEGORY_TO_GROUP = {}
for group, categories in CATEGORY_GROUPS.items():
    for category in categories:
        CATEGORY_TO_GROUP[category] = group

# For database storage - clean category names without prefixes
CLEAN_CATEGORY_NAMES = {
    "Entertainment: Books": "Books",
    "Entertainment: Film": "Movies", 
    "Entertainment: Music": "Music",
    "Entertainment: Musicals & Theatres": "Theater",
    "Entertainment: Television": "TV",
    "Entertainment: Video Games": "Video Games",
    "Entertainment: Board Games": "Board Games",
    "Entertainment: Comics": "Comics",
    "Entertainment: Japanese Anime & Manga": "Anime",
    "Entertainment: Cartoon & Animations": "Cartoons",
    "Science & Nature": "Nature",
    "Science: Computers": "Technology", 
    "Science: Mathematics": "Math",
    "Science: Gadgets": "Gadgets",
    "General Knowledge": "General",
    "History": "History",
    "Geography": "Geography",
    "Mythology": "Mythology", 
    "Art": "Art",
    "Politics": "Politics",
    "Sports": "Sports",
    "Animals": "Animals",
    "Vehicles": "Vehicles",
    "Celebrities": "Celebrities"
}

def get_category_group(category_name: str) -> str:
    """Get the main group for a specific category"""
    return CATEGORY_TO_GROUP.get(category_name, "General")

def get_clean_category_name(category_name: str) -> str:
    """Get a clean, short name for a category"""
    return CLEAN_CATEGORY_NAMES.get(category_name, category_name)

def get_categories_in_group(group_name: str) -> list:
    """Get all specific categories in a group"""
    return CATEGORY_GROUPS.get(group_name, [])

def get_all_groups() -> list:
    """Get all main category groups"""
    return list(CATEGORY_GROUPS.keys())

def get_balanced_category_selection(categories_per_group: int = 2) -> list:
    """Get a balanced selection of categories from all groups"""
    import random
    
    selected = []
    for group, categories in CATEGORY_GROUPS.items():
        # Randomly select categories from each group
        group_selection = random.sample(categories, min(categories_per_group, len(categories)))
        selected.extend(group_selection)
    
    return selected