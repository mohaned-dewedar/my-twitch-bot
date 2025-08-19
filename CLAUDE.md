# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CherryBott is a Twitch chatbot powered by local LLMs (via Ollama) that specializes in Smite2 knowledge and interactive trivia games. The bot listens to Twitch chat for messages wrapped in `{}` and trivia commands, responding with LLM-generated answers or managing trivia sessions.

## Development Commands

### Environment Setup
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment automatically
uv sync

# Activate the virtual environment (optional, uv run handles this automatically)
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Or run commands directly with uv (recommended)
uv run python chat_listener.py
```

### Database Management
```bash
# Start PostgreSQL database (required for leaderboards)
docker compose up -d

# Run database migrations
uv run alembic upgrade head

# Seed trivia questions (optional)
uv run python scripts/seed_questions.py
```

### Running the Bot
```bash
# Main bot entry point
uv run python chat_listener.py

# Alternative entry point for database testing
uv run python main.py
```

### Testing
```bash
# Run trivia functionality tests
uv run python test_trivia.py

# Run specific test files
uv run python tests/test_trivia_manager.py
uv run python tests/test_smite_handler.py

# Run tests with pytest (if available)
uv run pytest tests/
```

### Prerequisites
- Ollama server running with a model pulled (e.g., `ollama pull tinydolphin`)
- `.env` file with Twitch credentials:
  ```
  TWITCH_BOT_NAME=your_bot_username
  TWITCH_OAUTH_TOKEN=oauth:xxxxxxxxxxxxxxxxxxxxxx
  TWITCH_CHANNEL=your_channel_name
  ```

## Architecture Overview

### Core Components

**twitch/**: Twitch integration layer
- `irc_client.py`: Main WebSocket IRC client with rate limiting and command routing
- `message_parser.py`: Parses incoming Twitch PRIVMSG format

**llm/**: LLM integration and workers
- `ollama_manager.py`: Manages Ollama model lifecycle
- `ollama_worker.py`: Async worker queue for LLM prompt processing
- `trivia_handler.py`: Handles LLM-generated custom trivia questions

**trivia/**: Trivia game system
- `manager.py`: Central trivia session manager, handles active games and auto-mode
- `base.py`: Abstract base class for trivia handlers
- `types.py`: Concrete trivia implementations (API-based and Smite-specific)

**db/**: Database layer (PostgreSQL with asyncpg)
- `database.py`: Connection pool manager
- `models.py`: Database schema definitions
- Individual modules for channels, users, leaderboard, questions, sessions, attempts

**data/**: Static data and loaders
- `data_loader.py`: Loads Smite gods data from JSON files
- `category_loader.py`: Manages trivia categories
- `smite_gods_*.json`: Comprehensive Smite gods data with abilities

### Key Design Patterns

**Async Architecture**: Heavy use of asyncio throughout for handling concurrent Twitch messages, LLM processing, and database operations.

**Worker Queue Pattern**: `OllamaWorkerQueue` processes LLM prompts asynchronously to prevent blocking chat responses.

**Strategy Pattern**: `TriviaBase` abstract class with concrete implementations for different trivia types (API, Smite, Custom).

**State Management**: `TriviaManager` maintains active trivia sessions and handles transitions between single-question and auto-mode.

**Rate Limiting**: Built-in Twitch IRC rate limiting (18 messages per 30 seconds) in the IRC client.

## Trivia Commands

The bot supports these chat commands:
- `!trivia` - General trivia question
- `!trivia smite` - Smite-specific trivia
- `!trivia auto [smite]` - Continuous trivia mode
- `!answer <answer>` - Submit trivia answer
- `!giveup` - Reveal answer and end round
- `!end trivia` - Stop auto trivia mode
- `!trivia-help` - Show command help

## LLM Integration

Messages wrapped in `{}` (e.g., `{who is baron samedi}`) are sent to the configured Ollama model with a system prompt focused on Smite2 knowledge and concise, engaging responses.

## Database Schema

Uses Alembic migrations for schema management. Key tables include channels, users, trivia_sessions, questions, user_attempts, and leaderboard for tracking trivia performance across multiple Twitch channels.