# Data Directory

This directory contains trivia question data sources and management utilities.

## Files

**Question Data Sources:**
- `smite_gods_modified.json` - Smite god abilities data (256 questions)
- `smite_gods_extended.json` - Extended Smite data with additional metadata
- `trivia/custom_questions.json` - Custom MCQ, True/False, and basic questions
- `trivia_categories.json` - OpenTDB API category definitions

**Data Loaders:**
- `data_loader.py` - Core classes for loading questions from all sources
  - `SmiteDataStore` - Loads Smite JSON and creates ability-to-god mappings
  - `OpenTDBClient` - Fetches questions from OpenTDB API with rate limiting
  - `CustomTriviaLoader` - Loads custom questions from JSON files
- `category_loader.py` - Manages trivia categories from various sources

**Category Management:**
- `category_mapping.py` - Maps OpenTDB's 24+ categories into 4 clean groups:
  - **Entertainment** (Movies, TV, Games, Books, etc.)
  - **Science** (Technology, Nature, Math, etc.) 
  - **Culture** (History, Geography, Art, etc.)
  - **General** (Sports, Animals, Celebrities, etc.)

## Question Types

**Database Storage Format:**
- `multiple_choice` - MCQ with 4 options stored in `answer_options` JSONB
- `true_false` - Boolean questions with "true"/"false" answers
- `open_ended` - Free text answers (includes Smite god names)

**Categories:**
- `category` - Main group (Entertainment, Science, Culture, General)
- `subcategory` - Specific topic (Movies, Technology, History, etc.)

## Usage

Load questions into database:
```bash
# Load all sources (default)
uv run python -m scripts.load_questions

# Load specific sources  
uv run python -m scripts.load_questions --sources smite custom_json
uv run python -m scripts.load_questions --sources opentdb --amount 100

# Use balanced OpenTDB category selection
uv run python -m scripts.load_questions --sources opentdb --balanced --amount 50

# Show database statistics only
uv run python -m scripts.load_questions --stats-only
```