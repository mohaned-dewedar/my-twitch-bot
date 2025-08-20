CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    twitch_channel_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tier INT DEFAULT 0
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    twitch_username VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE question_banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    bank_id INT REFERENCES question_banks(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    options JSONB,
    difficulty INT DEFAULT 1,
    category VARCHAR(100),
    type VARCHAR(50), -- e.g., 'multiple_choice', 'true_false'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE, -- channel where the session is hosted
    user_id INT REFERENCES users(id) ON DELETE CASCADE, -- user who initiated the session
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' -- e.g., 'active', 'completed', 'abandoned'
);

CREATE TABLE attempts (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE, -- user who made this attempt
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE, -- for direct channel-user tracking
    user_answer TEXT, -- user's answer to the question
    is_correct BOOLEAN DEFAULT FALSE, -- whether the user's answer was correct
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Channel users association table for per-channel user stats
CREATE TABLE channel_users (
    id SERIAL PRIMARY KEY,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_questions INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    streak INT DEFAULT 0,
    best_streak INT DEFAULT 0,
    UNIQUE(channel_id, user_id)
);

-- Performance indexes
CREATE INDEX idx_attempts_user_channel ON attempts(user_id, channel_id);
CREATE INDEX idx_attempts_correct_answers ON attempts(is_correct) WHERE is_correct = TRUE;
CREATE INDEX idx_attempts_session ON attempts(session_id);
CREATE INDEX idx_attempts_question ON attempts(question_id);
CREATE INDEX idx_sessions_channel ON sessions(channel_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_bank ON questions(bank_id);
CREATE INDEX idx_channel_users_stats ON channel_users(channel_id, correct_answers DESC);
CREATE INDEX idx_channels_twitch_id ON channels(twitch_channel_id);

