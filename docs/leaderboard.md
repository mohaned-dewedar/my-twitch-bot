# Automatic Leaderboard and Score Tracking Implementation

## Overview

This document outlines the implementation of automatic leaderboard functionality for the CherryBott Twitch trivia bot. The system tracks user performance per channel and maintains real-time leaderboards with comprehensive statistics.

## Database Architecture (Already Implemented)

### Core Tables

**`channels`** - Twitch channel information
- `id` - Primary key
- `twitch_channel_id` - Twitch channel ID
- `name` - Channel name
- `tier` - Channel tier level

**`users`** - User information
- `id` - Primary key  
- `twitch_username` - Twitch username (unique)

**`channel_users`** - Per-channel user statistics (THE LEADERBOARD TABLE)
- Links users to channels with comprehensive stats
- `total_questions`, `correct_answers` - Overall performance
- `current_streak`, `best_streak` - Streak tracking
- `mcq_correct`, `tf_correct`, `open_correct` - Performance by question type
- `avg_response_time`, `fastest_correct_time` - Speed metrics
- `sessions_participated` - Engagement tracking

**`sessions`** - Trivia session tracking
- Tracks individual trivia sessions (single question, auto mode, tournaments)
- Links to channels and question banks
- Records session statistics and completion status

**`attempts`** - Individual answer attempts
- Every answer attempt is recorded here
- Links to sessions, questions, users, and channels
- Tracks correctness, response time, and answer method

**`questions`** - Question database with statistics
- Tracks `times_asked`, `times_correct`, `avg_response_time` per question

## Implementation Phases

### Phase 1: Database Integration (CURRENT)

#### 1.1 Trivia Handler Updates (`db/trivia_handlers.py`)
- Add channel_id, user_id, session_id parameters to handlers
- Modify `check_answer()` to record attempts using `create_attempt()`
- Automatic user stats updates via existing infrastructure

#### 1.2 IRC Client Integration (`twitch/irc_client.py`)
- Channel registration on startup (get/create channel record)
- Session management for auto vs single trivia modes
- User ID resolution (username → user_id) 
- Pass context to trivia handlers

#### 1.3 Session Lifecycle Management
- Create sessions when starting trivia (auto/single modes)
- Track session completion and statistics
- Handle session cleanup and final stats

### Phase 2: Chat Commands (FUTURE)

#### 2.1 Basic Commands
- `!leaderboard` / `!top` - Show top 10 users by correct answers
- `!stats` - Show personal statistics (total, accuracy, streaks)
- `!rank` - Show current leaderboard position
- `!streaks` - Show best streak holders

#### 2.2 Advanced Commands  
- `!leaderboard weekly` - Time-based rankings
- `!leaderboard smite` / `!leaderboard general` - Category-specific
- `!compare @username` - Head-to-head comparison

### Phase 3: Enhanced Features (FUTURE)

#### 3.1 Achievements System
- Streak milestones (5, 10, 25 consecutive correct answers)
- Accuracy achievements (90%+ with 50+ questions)
- Speed achievements (fastest response times)
- Category mastery tracking

#### 3.2 Advanced Analytics
- Performance trends over time
- Question difficulty analysis
- Peak activity periods
- Category preferences per user

## Leaderboard Types

### Overall Channel Leaderboards
**Primary ranking**: Based on total correct answers across all sessions
- Tracks lifetime performance in the channel  
- Includes accuracy percentage as tiebreaker
- Shows current and best streaks
- Performance by question type breakdown

### Session-Based Tracking
**Individual sessions**: Each trivia game is tracked separately
- Single question sessions
- Auto-trivia sessions (continuous play)  
- Tournament sessions (future)
- Session completion statistics

## Database Queries

### Top Leaderboard (Already Implemented)
```sql
SELECT u.twitch_username, cu.correct_answers, cu.total_questions,
       ROUND((cu.correct_answers::float / cu.total_questions::float) * 100, 1) as accuracy_pct,
       cu.best_streak, cu.current_streak
FROM channel_users cu
JOIN users u ON cu.user_id = u.id
WHERE cu.channel_id = $1 AND cu.total_questions > 0
ORDER BY cu.correct_answers DESC, accuracy_pct DESC
LIMIT 10
```

### User Stats and Ranking (Already Implemented)
```sql
WITH ranked_users AS (
    SELECT user_id, ROW_NUMBER() OVER (ORDER BY correct_answers DESC, 
           CASE WHEN total_questions > 0 THEN correct_answers::float / total_questions::float ELSE 0 END DESC) as rank
    FROM channel_users 
    WHERE channel_id = $1 AND total_questions > 0
)
SELECT rank FROM ranked_users WHERE user_id = $2
```

## Automatic Updates

### Real-Time Statistics
- **Every answer attempt** automatically updates:
  - User's total question count
  - Correct answer count (if applicable)
  - Current streak (incremented or reset)
  - Best streak (updated if current exceeds)
  - Question type-specific statistics
  - Response time averages

### Database Triggers (Already Implemented)
- Automatic `channel_users` updates via `create_attempt()` function
- Real-time leaderboard position updates
- Question statistics maintenance

## Integration Points

### Current Flow
1. User types `!answer <response>` 
2. IRC client calls `manager.submit_answer(answer, username)`
3. Manager calls `handler.check_answer(answer, username)`
4. Handler returns `(is_correct: bool, message: str)`

### New Flow (Phase 1)
1. User types `!answer <response>`
2. IRC client resolves username → user_id and gets channel_id
3. IRC client calls `manager.submit_answer(answer, username, user_id, channel_id, session_id)`
4. Manager calls `handler.check_answer(answer, username, user_id, channel_id, session_id)`
5. Handler calls `create_attempt()` to record in database
6. `create_attempt()` automatically calls `update_user_stats()` 
7. Leaderboard is updated in real-time

## Performance Considerations

### Optimizations (Already Implemented)
- Indexed queries for fast leaderboard retrieval
- Optimized `channel_users` table avoids expensive aggregations
- Efficient user ranking queries with window functions

### Scalability
- Per-channel separation prevents cross-contamination
- Database connection pooling for concurrent users
- Minimal overhead per answer attempt

## Migration Strategy

### Database Changes
- ✅ Schema already supports full functionality
- ✅ All required tables and indexes exist
- ✅ No migrations needed for Phase 1

### Code Changes
- Modify trivia handlers to accept and use database parameters
- Update IRC client to manage channels, users, and sessions
- Maintain backward compatibility during transition

## Testing Strategy

### Unit Tests
- Test automatic stat updates with mock database
- Verify correct/incorrect answer tracking
- Test streak calculation logic

### Integration Tests  
- End-to-end answer flow with real database
- Multi-user scenario testing
- Channel separation verification

### Performance Tests
- Concurrent user handling
- Database query performance under load
- Memory usage during long auto-trivia sessions

## Future Enhancements

### Real-Time Features
- Live leaderboard updates during active trivia
- Streak announcements for milestones
- Personal best notifications

### Social Features
- Team/clan support for group competition
- Challenge system between users
- Tournament bracket management

### Analytics Dashboard
- Web interface for detailed statistics
- Historical performance graphs  
- Channel moderator insights

## Implementation Notes

### Error Handling
- Graceful fallback if database is unavailable
- Continue trivia functionality even without tracking
- Proper logging of database errors

### Privacy Considerations  
- No personally identifiable information stored
- Users can opt out of tracking (future feature)
- Channel-specific data isolation

### Maintenance
- Regular database cleanup of old sessions
- Performance monitoring and optimization
- Backup strategy for leaderboard data