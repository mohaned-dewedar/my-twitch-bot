# CherryBott Web Dashboard

A FastAPI-powered web overlay system for displaying real-time leaderboards in OBS streaming software.

## Quick Start

### 1. Start the Web Dashboard

```bash
# Basic startup (runs on http://localhost:8080)
python start_web_dashboard.py

# Custom port
python start_web_dashboard.py --port 3000

# Development mode with auto-reload
python start_web_dashboard.py --dev
```

### 2. Set Up OBS Browser Source

1. **Add Browser Source** in OBS
2. **Set URL**: `http://localhost:8080/overlay/your_channel_name`
3. **Set Dimensions**: 600x400 (or adjust to fit your layout)
4. **Check**: "Shutdown source when not visible"
5. **Check**: "Refresh browser when scene becomes active"

## Available URLs

### For OBS Overlay
- **Main overlay**: `http://localhost:8080/overlay/{channel_name}`
- **Compact mode**: `http://localhost:8080/overlay/{channel_name}?compact=true`
- **Custom limit**: `http://localhost:8080/overlay/{channel_name}?limit=10`
- **Custom refresh**: `http://localhost:8080/overlay/{channel_name}?refresh=30`

### For Preview/Testing
- **Preview overlay**: `http://localhost:8080/overlay/{channel_name}/preview`
- **JSON API**: `http://localhost:8080/api/leaderboard/{channel_name}`

### Examples
```
http://localhost:8080/overlay/thecherryo
http://localhost:8080/overlay/thecherryo?compact=true&limit=3
http://localhost:8080/overlay/thecherryo/preview
```

## Features

### 🎨 **Multiple Display Modes**
- **Standard**: Full leaderboard with stats and streaks
- **Compact**: Minimal space usage for smaller overlays
- **Preview**: Browser-friendly version with OBS setup instructions

### 🔄 **Auto-Refresh**
- Configurable refresh intervals (5-300 seconds)
- Automatic error handling and retry logic
- Connection status indicators

### 🎭 **OBS Optimized**
- Transparent backgrounds
- High contrast text with shadows
- Scalable design for different overlay sizes
- Smooth animations and transitions

### 📊 **Rich Data Display**
- User rankings with medal icons (🥇🥈🥉)
- Correct/total answers with accuracy percentages
- Current and best streak indicators
- Real-time channel statistics

## Customization Options

### URL Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `limit` | 5 | Number of leaderboard entries (1-20) |
| `compact` | false | Use compact display mode |
| `refresh` | 15 | Auto-refresh interval in seconds (5-300) |
| `theme` | default | Visual theme (planned feature) |

### Example Configurations

**Sidebar overlay** (narrow space):
```
http://localhost:8080/overlay/your_channel?compact=true&limit=3
```

**Main overlay** (prominent display):
```
http://localhost:8080/overlay/your_channel?limit=10&refresh=10
```

**Bottom banner** (wide, short):
```
http://localhost:8080/overlay/your_channel?compact=true&limit=5
```

## API Endpoints

### GET `/api/leaderboard/{channel_name}`
Returns JSON leaderboard data.

**Response Example**:
```json
{
  "channel": {
    "channel_name": "thecherryo",
    "channel_id": 1,
    "total_users": 1,
    "total_questions": 12
  },
  "users": [
    {
      "twitch_username": "thecherryo",
      "correct_answers": 5,
      "total_questions": 12,
      "accuracy_pct": 41.7,
      "current_streak": 2,
      "best_streak": 2,
      "rank": 1
    }
  ],
  "timestamp": "2025-08-29T18:23:49.836798Z",
  "limit": 5
}
```

### GET `/health`
Health check endpoint for monitoring.

## Troubleshooting

### Common Issues

**"Channel not found"**
- Ensure the channel name matches exactly (case-insensitive)
- Channel must have trivia data in the database

**Overlay not refreshing**
- Check browser console for JavaScript errors
- Verify API endpoint is accessible
- Try refreshing the browser source in OBS

**Styling issues**
- CSS is optimized for OBS Browser Source
- Some styles may appear different in regular browsers
- Use `/preview` endpoint for browser testing

### Performance Tips

- Use appropriate refresh intervals (15-30 seconds recommended)
- Enable "Shutdown source when not visible" in OBS
- Consider using compact mode for multiple overlays

## Development

### Project Structure
```
web/
├── main.py              # FastAPI application
├── models/              # Pydantic data models
├── routers/             # API route handlers
├── services/            # Business logic
├── templates/           # Jinja2 HTML templates
├── static/              # CSS and JavaScript assets
└── dependencies.py      # FastAPI dependencies
```

### Adding New Features
1. Add Pydantic models in `web/models/`
2. Create business logic in `web/services/`
3. Add routes in `web/routers/`
4. Create templates in `web/templates/`
5. Update CSS/JS in `web/static/`

### Testing
```bash
# Start in development mode
python start_web_dashboard.py --dev

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/leaderboard/your_channel
```