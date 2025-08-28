-- Improved schema with better question type support and source tracking

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

-- Enhanced question banks with source tracking
CREATE TABLE question_banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL, -- 'smite_data', 'opentdb_api', 'custom_json'
    source_config JSONB, -- API endpoints, file paths, generation parameters
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Enhanced questions table with better type support
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    bank_id INT REFERENCES question_banks(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- 'multiple_choice', 'true_false', 'open_ended'
    
    -- Answer storage - different formats for different types
    correct_answer TEXT NOT NULL,
    answer_options JSONB, -- For MCQ: ["option1", "option2", "option3", "option4"]
    
    -- Metadata
    category VARCHAR(100),
    subcategory VARCHAR(100), -- For more granular categorization (e.g., 'smite' for open_ended)
    difficulty INT DEFAULT 1, -- 1=easy, 2=medium, 3=hard
    tags TEXT[], -- Array of tags for flexible categorization
    
    -- Source tracking
    source_id VARCHAR(255), -- External ID from API or file
    source_data JSONB, -- Original data from source for reference
    
    -- Statistics
    times_asked INT DEFAULT 0,
    times_correct INT DEFAULT 0,
    avg_response_time DECIMAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_question_type CHECK (question_type IN ('multiple_choice', 'true_false', 'open_ended')),
    CONSTRAINT mcq_needs_options CHECK (
        question_type != 'multiple_choice' OR 
        (answer_options IS NOT NULL AND jsonb_array_length(answer_options) >= 2)
    ),
    CONSTRAINT tf_valid_answer CHECK (
        question_type != 'true_false' OR 
        correct_answer IN ('true', 'false')
    )
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    session_type VARCHAR(50) DEFAULT 'single', -- 'single', 'auto', 'tournament'
    question_bank_id INT REFERENCES question_banks(id) ON DELETE SET NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'abandoned'
    total_questions INT DEFAULT 0,
    total_correct INT DEFAULT 0
);

CREATE TABLE attempts (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INT REFERENCES questions(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE,
    
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    response_time_seconds DECIMAL, -- Time taken to answer
    answer_method VARCHAR(50), -- 'letter_shortcut', 'full_text', 'fuzzy_match'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced channel users with more detailed stats
CREATE TABLE channel_users (
    id SERIAL PRIMARY KEY,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Overall stats
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_questions INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    
    -- Streak tracking
    current_streak INT DEFAULT 0,
    best_streak INT DEFAULT 0,
    
    -- Performance by question type
    mcq_correct INT DEFAULT 0,
    mcq_total INT DEFAULT 0,
    tf_correct INT DEFAULT 0,
    tf_total INT DEFAULT 0,
    open_correct INT DEFAULT 0,
    open_total INT DEFAULT 0,
    
    -- Speed tracking
    avg_response_time DECIMAL,
    fastest_correct_time DECIMAL,
    
    -- Engagement
    sessions_participated INT DEFAULT 0,
    favorite_category VARCHAR(100),
    
    UNIQUE(channel_id, user_id)
);

-- Source metadata tracking for data freshness
CREATE TABLE source_metadata (
    id SERIAL PRIMARY KEY,
    bank_id INT REFERENCES question_banks(id) ON DELETE CASCADE,
    source_identifier VARCHAR(255) NOT NULL, -- file path, API endpoint, etc.
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP,
    checksum VARCHAR(64), -- For detecting file changes
    record_count INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'error', 'deprecated'
    error_message TEXT,
    metadata JSONB -- Source-specific data like API tokens, rate limits, etc.
);

-- Performance indexes
CREATE INDEX idx_questions_type_category ON questions(question_type, category);
CREATE INDEX idx_questions_subcategory ON questions(subcategory);
CREATE INDEX idx_questions_bank_active ON questions(bank_id) WHERE id IS NOT NULL;
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_tags ON questions USING GIN(tags);
CREATE INDEX idx_questions_stats ON questions(times_asked, times_correct);

CREATE INDEX idx_attempts_user_channel ON attempts(user_id, channel_id);
CREATE INDEX idx_attempts_correct_answers ON attempts(is_correct) WHERE is_correct = TRUE;
CREATE INDEX idx_attempts_session ON attempts(session_id);
CREATE INDEX idx_attempts_question ON attempts(question_id);
CREATE INDEX idx_attempts_time ON attempts(created_at);

CREATE INDEX idx_sessions_channel ON sessions(channel_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_type ON sessions(session_type);

CREATE INDEX idx_channel_users_stats ON channel_users(channel_id, correct_answers DESC);
CREATE INDEX idx_channel_users_streak ON channel_users(channel_id, best_streak DESC);
CREATE INDEX idx_channels_twitch_id ON channels(twitch_channel_id);

CREATE INDEX idx_question_banks_source ON question_banks(source_type, is_active);
CREATE INDEX idx_source_metadata_status ON source_metadata(status, last_checked);

-- Function to update question stats
CREATE OR REPLACE FUNCTION update_question_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE questions 
    SET times_asked = times_asked + 1,
        times_correct = times_correct + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.question_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update question stats
CREATE TRIGGER trigger_update_question_stats
    AFTER INSERT ON attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_question_stats();

-- Function to update user stats
CREATE OR REPLACE FUNCTION update_channel_user_stats()
RETURNS TRIGGER AS $$
DECLARE
    q_type VARCHAR(50);
BEGIN
    -- Get question type
    SELECT question_type INTO q_type FROM questions WHERE id = NEW.question_id;
    
    -- Update or insert channel_users record
    INSERT INTO channel_users (channel_id, user_id, total_questions, correct_answers, last_seen)
    VALUES (NEW.channel_id, NEW.user_id, 1, CASE WHEN NEW.is_correct THEN 1 ELSE 0 END, NEW.created_at)
    ON CONFLICT (channel_id, user_id) 
    DO UPDATE SET
        total_questions = channel_users.total_questions + 1,
        correct_answers = channel_users.correct_answers + CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        last_seen = NEW.created_at,
        -- Update type-specific stats
        mcq_total = CASE WHEN q_type = 'multiple_choice' THEN channel_users.mcq_total + 1 ELSE channel_users.mcq_total END,
        mcq_correct = CASE WHEN q_type = 'multiple_choice' AND NEW.is_correct THEN channel_users.mcq_correct + 1 ELSE channel_users.mcq_correct END,
        tf_total = CASE WHEN q_type = 'true_false' THEN channel_users.tf_total + 1 ELSE channel_users.tf_total END,
        tf_correct = CASE WHEN q_type = 'true_false' AND NEW.is_correct THEN channel_users.tf_correct + 1 ELSE channel_users.tf_correct END,
        open_total = CASE WHEN q_type = 'open_ended' THEN channel_users.open_total + 1 ELSE channel_users.open_total END,
        open_correct = CASE WHEN q_type = 'open_ended' AND NEW.is_correct THEN channel_users.open_correct + 1 ELSE channel_users.open_correct END;
        
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update user stats
CREATE TRIGGER trigger_update_channel_user_stats
    AFTER INSERT ON attempts
    FOR EACH ROW
    EXECUTE FUNCTION update_channel_user_stats();