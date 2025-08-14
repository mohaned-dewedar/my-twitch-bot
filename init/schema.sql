Create Table channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tier INT DEFAULT 0
);

Create Table users (
    id SERIAL PRIMARY KEY,
    twitch_username VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Create Table question_banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

Create Table question (
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

Create Table sessions (
    id SERIAL PRIMARY KEY,
    channel_id INT REFERENCES channels(id) ON DELETE CASCADE, -- channel where the session is hosted
    user_id INT REFERENCES users(id) ON DELETE CASCADE, -- user who initiated the session
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' -- e.g., 'active', 'completed', 'abandoned'
);

Create Table attempts (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions(id) ON DELETE CASCADE,
    question_id INT REFERENCES question(id) ON DELETE CASCADE,
    user_answer TEXT, -- user's answer to the question
    is_correct BOOLEAN DEFAULT FALSE, -- whether the user's answer was correct
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

