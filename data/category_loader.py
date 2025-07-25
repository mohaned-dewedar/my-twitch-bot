import os
import requests
import json

CATEGORY_FILE = "data/trivia_categories.txt"
CATEGORY_URL = "https://opentdb.com/api_category.php"


def load_trivia_categories() -> list:
    """
    Load trivia categories from a local file, or fetch and save them if not cached.
    Returns a list of category names.
    """
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, "r") as f:
            categories = [line.strip() for line in f.readlines()]
            if categories:
                return categories

    # Fetch from API
    response = requests.get(CATEGORY_URL)
    if response.status_code != 200:
        raise RuntimeError("Failed to fetch categories from OpenTDB")

    data = response.json()
    categories = [item["name"] for item in data.get("trivia_categories", [])]

    # Save to file
    os.makedirs(os.path.dirname(CATEGORY_FILE), exist_ok=True)
    with open(CATEGORY_FILE, "w") as f:
        for name in categories:
            f.write(name + "\n")

    return categories


def save_trivia_categories_json(json_path="data/trivia_categories.json"):
    """
    Fetch and save trivia categories as a JSON file with name and ID.
    """
    response = requests.get(CATEGORY_URL)
    if response.status_code != 200:
        raise RuntimeError("Failed to fetch categories from OpenTDB")
    data = response.json()
    categories = data.get("trivia_categories", [])
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(categories, f, indent=2)
    return categories


if __name__ == "__main__":
    cats = load_trivia_categories()
    print("Available Trivia Categories:")
    for c in cats:
        print("-", c)
    # Save as JSON with IDs
    save_trivia_categories_json()
    print("Saved categories as JSON with IDs.")
