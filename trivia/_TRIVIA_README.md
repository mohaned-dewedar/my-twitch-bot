# Smite Trivia Bot

This Twitch bot includes a Smite trivia system that allows viewers to test their knowledge of Smite gods and abilities.

## Features

- **Ability-to-God Mapping**: The bot loads comprehensive data about all Smite gods and their abilities
- **Interactive Trivia**: Viewers can participate in trivia games by guessing which god owns a specific ability
- **Real-time Responses**: The bot responds immediately to trivia commands and answers
- **Case-insensitive Matching**: Answers are accepted regardless of capitalization

## How It Works

### Starting a Trivia Game
Any viewer can start a trivia game by typing:
```
{trivia-ability}
```

The bot will respond with a random ability and ask viewers to guess which god owns it.

### Answering Trivia
Viewers can answer by typing:
```
{trivia-god name}
```

For example:
- `{trivia-Zeus}`
- `{trivia-Thor}`
- `{trivia-Hercules}`

## New Functionality: Auto Trivia Mode

You can now run trivia games continuously in chat! When a user types:
- `!trivia auto` — The bot will keep asking general trivia questions one after another until someone ends the session.
- `!trivia auto smite` — The bot will keep asking Smite trivia questions until ended.

To stop auto trivia mode, type:
- `!end trivia` — This will end the current auto trivia session.

### How Auto Mode Works
- The bot automatically asks a new question as soon as the previous one is answered correctly.
- All answer options are shown in chat, formatted with emojis for readability (e.g., 🇦 Option1 🇧 Option2 ...).
- Works for both general and Smite trivia.
- You can still use single-round commands (`!trivia`, `!trivia smite`) for one-off questions.

## Data Structure

The system uses an extended version of the Smite gods data (`data/smite_gods_extended.json`) that includes:
- God names
- Ability names
- Image URLs
- Profile URLs

## Files

- `data_loader.py` - Main class for loading and managing Smite data
- `trivia_handler.py` - Handles trivia game logic and chat interactions
- `data/smite_gods_extended.json` - Extended data file with abilities
- `test_trivia.py` - Test script to verify functionality

## Integration

The trivia system is integrated into the existing Twitch IRC client (`twitch/irc_client.py`) and will automatically:
1. Load the Smite data when the bot starts
2. Monitor chat for trivia commands
3. Handle trivia games and responses
4. Continue supporting existing LLM functionality

## Testing

Run the test script to verify everything works:
```bash
python3 test_trivia.py
```

## Commands Summary

| Command                | Description                                 |
|------------------------|---------------------------------------------|
| `!trivia`              | Start a general trivia question             |
| `!trivia smite`        | Start a Smite trivia question               |
| `!trivia auto`         | Start continuous general trivia             |
| `!trivia auto smite`   | Start continuous Smite trivia               |
| `!answer <your answer>`| Submit your answer to the current question  |
| `!giveup`              | End the current trivia round and reveal answer |
| `!end trivia`          | End auto trivia mode                        |
| `!trivia-help`         | Show help for trivia commands               |

## Technical Details

- **Data Loading**: Happens once when the bot starts
- **Memory Efficient**: All data is loaded into memory for fast lookups
- **Thread Safe**: Designed to handle multiple concurrent users
- **Error Handling**: Graceful handling of missing data or invalid inputs

## Future Enhancements

Potential improvements could include:
- Score tracking for viewers
- Multiple difficulty levels
- Ability to ask about specific gods
- Cooldown periods between trivia games
- Leaderboards