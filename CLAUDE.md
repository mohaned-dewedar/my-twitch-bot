# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CherryBott is a Twitch chatbot with multiple capabilities:
1. Interactive trivia system (general knowledge + Smite-specific)
2. Local LLM integration via Ollama (legacy, not actively used)
3. External chat API integration for Q&A (`!ask` and `!chat` commands)

## Development Commands

### Setup
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Start PostgreSQL database (for leaderboards/tracking)
docker compose up -d

# Run database migrations
uv run alembic upgrade head
```

### Running the Bot
```bash
# Main bot entry point
uv run python chat_listener.py

# Alternative: direct IRC client
uv run python twitch/irc_client.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific tests with verbose output
uv run pytest tests/test_trivia_manager.py -v
uv run pytest tests/test_smite_handler.py -v
```

### Database Operations
```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Load questions into database
uv run python -m scripts.load_questions

# Load specific question sources
uv run python -m scripts.load_questions --sources smite custom_json
uv run python -m scripts.load_questions --sources opentdb --amount 50 --balanced

# Show database statistics
uv run python -m scripts.load_questions --stats-only
```

## Architecture

### Main Entry Point
**`chat_listener.py`** - Simple wrapper that creates and runs IRCClient
**`twitch/irc_client.py`** - Core bot implementation with all functionality

### Key Components

**IRC Client** (`twitch/irc_client.py:IRCClient`)
- WebSocket connection to Twitch IRC (`wss://irc-ws.chat.twitch.tv:443`)
- Command routing system with exact and prefix matching
- Rate limiting (18 messages per 30-second window)
- Auto-reconnection with exponential backoff

**Trivia System** (`trivia/`)
- `manager.py` - Session state management, answer checking
- `types.py` - ApiTriviaHandler (OpenTDB API) and SmiteTriviaHandler (local data)
- Support for both single-question and auto-continuous modes
- Multiple choice format with emoji indicators (🇦 🇧 🇨 🇩)

**Question Database System** (`data/`, `scripts/`)
- PostgreSQL storage with organized categories and question banks
- 4 main categories: Entertainment, Science, Culture, General
- Support for multiple question types: multiple_choice, true_false, open_ended
- Data sources: Smite abilities (256), Custom JSON, OpenTDB API
- Smart category mapping groups OpenTDB's 24+ categories into clean groups

**External API Integration**
- HTTP requests to `localhost:8000/chat` endpoint for AI responses
- Markdown stripping for Twitch chat compatibility
- Async request handling with proper error management

**Database Layer** (`db/`)
- PostgreSQL with asyncpg connection pooling
- SQLAlchemy models for users, channels, leaderboards, attempts, questions, question_banks
- Enhanced schema with question statistics, user performance tracking
- Automatic triggers for updating question/user stats
- Alembic migrations for schema management

### Message Flow

1. WebSocket receives Twitch IRC messages
2. `parse_privmsg()` extracts username and message content  
3. `_dispatch_command()` routes to appropriate command handler
4. Commands return response strings that are sent back to chat
5. Rate limiting applied before sending to Twitch

### Chat Commands

**Trivia Commands:**
- `!trivia` - Start single general trivia question (MCQ format)
- `!trivia smite` - Start single Smite god ability question  
- `!trivia auto` - Start continuous general trivia mode
- `!trivia auto smite` - Start continuous Smite trivia mode
- `!answer <answer>` - Submit answer (supports letter shortcuts: a/b/c/d)
- `!giveup` - End current question and show answer
- `!end trivia` - Stop auto trivia mode
- `!trivia-help` - Show help text

**AI Chat Commands:**
- `!ask <question>` - Send question to external chat API
- `!chat <question>` - Alternative to !ask command

### Configuration

Required environment variables in `.env`:
- `TWITCH_BOT_NAME` - Bot username
- `TWITCH_OAUTH_TOKEN` - OAuth token with `chat:read chat:edit user:write:chat` scopes
- `TWITCH_CHANNEL` - Target channel name
- `DATABASE_URL` - PostgreSQL connection string (default: postgresql://trivia:trivia-password@localhost:5432/trivia)

### Auto Trivia Mode

When in auto mode (`!trivia auto` or `!trivia auto smite`):
- Correct answers automatically trigger the next question (1-second delay)
- `!giveup` shows answer and immediately starts next question
- Mode persists until `!end trivia` or manual single-question commands

### Answer Processing

For MCQ questions, users can answer with:
- Full answer text: `!answer The Great Wall of China`
- Letter shortcuts: `!answer a`, `!answer b`, etc.
- Letters are mapped to answer array indices automatically

### Rate Limiting

Token bucket implementation:
- Maximum 18 messages per 30-second sliding window
- Automatic sleep/delay when limit reached
- Message length clamped to 450 characters for Twitch compatibility

## Database Schema

### Question Organization

**Question Banks** - Organized by source type:
- `smite_data` - Smite god ability questions (256 questions)
- `custom_json` - Custom questions from JSON files
- `opentdb_api` - Questions from OpenTDB API organized by category groups

**Categories** - 4 main groups with clean subcategories:
- **Entertainment**: Movies, TV, Games, Books, Comics, Anime, etc.
- **Science**: Technology, Nature, Math, Gadgets
- **Culture**: History, Geography, Art, Mythology, Politics  
- **General**: Sports, Animals, Vehicles, Celebrities

**Question Types**:
- `multiple_choice` - MCQ with 4 options stored in JSONB `answer_options`
- `true_false` - Boolean questions with normalized "true"/"false" answers
- `open_ended` - Free text answers (includes Smite god names)

### Statistics & Leaderboards

**Automatic Tracking**:
- Question statistics: times_asked, times_correct, avg_response_time
- User performance: total questions, correct answers, streaks
- Type-specific stats: MCQ vs True/False vs Open-ended performance
- Channel-specific leaderboards with per-user rankings

**Database Triggers**:
- Auto-update question stats on each attempt
- Auto-update user stats and streaks
- Real-time leaderboard calculations