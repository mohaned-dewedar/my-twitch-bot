# 🍒 CherryBott Automated Launcher Guide

## 🚀 Quick Start (Recommended)

The easiest way to set up and run CherryBott is with the automated launcher:

### For Linux/macOS:
```bash
./start.sh
```

### For Windows:  
```batch
start.bat
```

### Or directly with Python:
```bash
python3 launcher.py
```

## 📋 What the Launcher Does

The automated launcher streamlines your entire setup process:

### 🎯 **Quick Start Mode** (Option 1)
Fully automated setup that:
1. ✅ Checks environment (uv, Twitch CLI, Chrome)  
2. ✅ Initializes uv environment and dependencies
3. ✅ Detects Chrome profiles for bot account
4. ✅ Generates Twitch OAuth token automatically
5. ✅ Updates `.env` file with credentials
6. ✅ Sets up PostgreSQL database  
7. ✅ Loads trivia questions
8. ✅ Starts the bot

### 🔧 **Manual Setup Mode** (Option 2)  
Step-by-step guided setup with prompts

### 🔑 **Token Generator** (Option 3)
Just generates a new Twitch token and updates `.env`

### ▶️ **Start Bot** (Option 4)
Skip setup and launch the bot directly

### 🔍 **Status Check** (Option 5)
Check if everything is configured properly

## 🛠️ Before First Run

### 1. Install Required Tools

**uv (Package Manager):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Twitch CLI (Optional but Recommended):**
- Follow: https://dev.twitch.tv/docs/cli/
- Enables fully automated token generation

**Docker (for Database):**
- Install Docker and Docker Compose

### 2. Twitch Developer Setup

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Create a new application
3. Save your Client ID and Client Secret
4. Configure Twitch CLI (if installed):
   ```bash
   twitch configure
   ```

## 🎮 Usage Scenarios

### Scenario 1: First Time Setup (Fully Automated)
```bash
./start.sh
# Select: 1 (Quick Start)
# Follow prompts for Chrome profile
# Token generated automatically
# Bot starts automatically
```

### Scenario 2: Token Expired
```bash
./start.sh  
# Select: 3 (Generate New Token Only)
# New token generated and saved
# Select: 4 (Start Bot)
```

### Scenario 3: Manual Control
```bash
./start.sh
# Select: 2 (Manual Setup)
# Go through each step individually
# More control over the process
```

## 🤖 Chrome Profile Management

The launcher can:
- **Auto-detect** Chrome profiles
- **Launch Chrome** with the correct bot profile
- **Handle multiple** Chrome installations

### Profile Selection:
1. **Default Profile**: Standard Chrome profile
2. **Profile 1, 2, etc.**: Additional Chrome profiles  
3. **Manual**: You'll open Chrome yourself

💡 **Tip**: Create a dedicated Chrome profile for your bot account to avoid token conflicts.

## 🔧 Troubleshooting

### "uv not found"
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

### "Twitch CLI not found"  
- Install from: https://dev.twitch.tv/docs/cli/
- Or use manual token generation (launcher will guide you)

### "Database connection failed"
```bash  
docker compose up -d  # Start database manually
docker compose ps     # Check if running
```

### "Chrome not found"
- Install Google Chrome or Chromium
- Or use manual token generation

### Token Issues
```bash
./start.sh
# Select: 3 (Generate New Token Only)
# This will refresh your token
```

## 📁 File Structure After Setup

```
twitch/
├── launcher.py          # Main launcher script
├── start.sh            # Linux/macOS wrapper
├── start.bat           # Windows wrapper  
├── .env                # Your credentials (created by launcher)
├── chat_listener.py    # Bot entry point
└── ...
```

## ⚙️ Configuration Files

### `.env` (Created Automatically)
```bash
TWITCH_BOT_NAME=your_bot_username
TWITCH_OAUTH_TOKEN=oauth:your_token_here
TWITCH_CHANNEL=your_channel_name
DATABASE_URL=postgresql://trivia:trivia-password@localhost:5432/trivia
```

## 🎯 Advanced Usage

### Environment Variables Override
```bash
export TWITCH_CHANNEL="different_channel"
./start.sh
```

### Custom Database URL
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
./start.sh  
```

### Debug Mode
```bash
export DEBUG=1
./start.sh
```

## 🆘 Support

If you encounter issues:

1. **Check Status**: Run launcher → Option 5
2. **View Logs**: Check terminal output  
3. **Manual Fallback**: Use the original README instructions
4. **Database Issues**: Run `scripts/inspect_database.py`

## 🚀 What's New

The launcher eliminates the old manual process:

### ❌ Old Way:
1. Manually install uv
2. Manually get Twitch token with specific Chrome profile
3. Manually copy token to .env  
4. Manually start database
5. Manually run migrations
6. Manually load questions
7. Manually start bot

### ✅ New Way:
```bash
./start.sh
# Select 1
# Done! 🎉
```

---

**🍒 CherryBott is now ready to run with just one command!**