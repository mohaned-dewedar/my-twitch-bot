# 🧠 CherryBott — Twitch x LLM Smite Bot

**CherryBott** is a Twitch chatbot powered by local LLMs (via [Ollama](https://ollama.com)) that answers `{chat}` messages with fun and helpful responses . I will be utilizing to integrate fun games like trivia in my chat aswell as answer question about Smite2 Gods and Patchnotes

![CherryBott Example Response](example.png)
---

## 🚀 Features

- 💬 Chat-based Q&A directly in Twitch with external API integration
- 🎲 **Database-driven trivia system** with organized categories and leaderboards
- 🕹️ **Smite2 trivia** - 256+ questions about god abilities
- 📊 **Multiple question types**: Multiple choice, True/False, Open-ended
- 🏆 **User statistics & leaderboards** with automatic tracking
- 🤖 Local LLM-powered answers using [Ollama](https://ollama.com) (legacy)

---

## 🧰 Requirements

- Python 3.9+
- PostgreSQL database (via Docker)
- Twitch account and [OAuth token](https://twitchapps.com/tmi/)
- Optional: [Ollama installed](https://ollama.com) for local LLM features

---

## 🔧 Setup 

### 1. Clone the Repo

```bash
git clone https://github.com/mohaned-dewedar/my-twitch-bot
cd my-twitch-bot
```
### 2. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Dependencies
```bash
# This will automatically create a virtual environment and install dependencies
uv sync
```

### 4. Start Database
```bash
# Start PostgreSQL database
docker compose up -d

# Run database migrations
uv run alembic upgrade head

# Load trivia questions into database
uv run python -m scripts.load_questions
```

### 5. Configure Twitch Credentials 
Create a .env file in the project root:

```bash
TWITCH_BOT_NAME=your_bot_username
TWITCH_OAUTH_TOKEN=oauth:xxxxxxxxxxxxxxxxxxxxxx
TWITCH_CHANNEL=your_channel_name
```
#### 🔐 How to Get a Twitch OAuth Token

1. Go to [https://dev.twitch.tv/](https://dev.twitch.tv/) and create a **Twitch Developer account**
2. Create a new **Application**  
   - Choose **Confidential** as the application type (not Public)
3. Save your **Client ID** and **Client Secret** — you’ll need them to generate a token

---

#### 🔧 Install Twitch CLI

Follow the official guide to install the Twitch CLI:  
[https://dev.twitch.tv/docs/cli/](https://dev.twitch.tv/docs/cli/)

Once installed, run the following command to generate a user token:

```bash
twitch token -u --scopes "chat:read chat:edit user:write:chat"
```
Copy the Authentication token at User Access Token : {token}

### 6. Run the Bot
```bash
uv run python chat_listener.py
```

### How it works:
**Trivia System:**
- `!trivia` - Start general knowledge questions
- `!trivia smite` - Start Smite god ability questions  
- `!trivia auto` - Start continuous trivia mode
- `!answer <your answer>` - Submit answers (supports letter shortcuts: a/b/c/d)
- `!giveup` - End current question and show answer

**AI Chat Integration:**
- `!ask <question>` - Send questions to external chat API
- `!chat <question>` - Alternative chat command

* Applies a system prompt like:

> "You are CherryBott. You answer general questions, specialize in Smite2, and keep responses short, fun, and engaging. Do not ask follow-up questions."

* Sends the response back to Twitch chat

## 🎲 Trivia Functionality in Chat

CherryBott supports interactive trivia games directly in Twitch chat! Users can play general trivia or Smite-specific trivia using simple commands:

### Commands
- `!trivia` — Start a general trivia question (multiple choice, easy difficulty)
- `!trivia smite` — Start a Smite gods trivia question
- `!answer <your answer>` — Submit your answer to the current trivia question
- `!giveup` — End the current trivia round and reveal the answer
- `!trivia-help` — Show help for trivia commands

### How Trivia Appears in Chat
- Questions are sent with all answer options, clearly formatted with emojis for readability (e.g., 🇦 Option1 🇧 Option2 ...)
- Smite trivia asks you to name the god for a given ability
- General trivia uses easy questions from OpenTDB or custom questions

Enjoy competing with your chat and see who knows the most!

### 🧪 WIP / Future Tooling

Planned features to enhance CherryBott's intelligence and usability:

#### 🔍 Tool Integration
- ✅ Google Search (real-time lookups)
- ✅ `tracker.gg` API for live player stats or rankings
- ✅ Smite wiki and patch notes loader (RAG KB)

#### 🧠 Memory
- 🕒 Short-term memory during a Twitch session
- 🧾 Long-term user-specific memory (basic vector DB)

#### 🔗 Model Abstraction
- 🌐 Use **more powerful models via HTTP APIs** (e.g., GPT, Mixtral, etc.)
- 🔄 Swap between Ollama models or remote endpoints dynamically

---

### 🛠️ TODO & Improvements

- [ ] `.txt` file or UI to change the system prompt without code edits  
- [ ] Configurable model swapping (via `.env` or CLI args)  
- [ ] Packaged `.exe` or launcher for non-technical users  
- [ ] Web dashboard to monitor or test prompts outside of Twitch  
- [ ] Modularize LLM logic into a shared package (`smite-chat-core`)  

I will most likely stop working on this for a bit to scrape and gather the needed information to make this viable for RAG and make it useful for my chat then come back to this.
