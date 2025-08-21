from sqlalchemy import (
    Table, Column, Integer, String, Text, TIMESTAMP, DECIMAL, ARRAY,
    ForeignKey, Boolean, MetaData, func, text, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

channels = Table(
    "channels",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("twitch_channel_id", String(255), nullable=False, unique=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("tier", Integer, server_default=text("0")),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("twitch_username", String(255), nullable=False, unique=True),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
)

question_banks = Table(
    "question_banks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("source_type", String(50), nullable=False),  # 'smite_data', 'opentdb_api', 'custom_json'
    Column("source_config", JSONB),  # API endpoints, file paths, generation parameters
    Column("last_updated", TIMESTAMP, server_default=func.current_timestamp()),
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("is_active", Boolean, server_default=text("true")),
)

questions = Table(
    "questions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bank_id", Integer, ForeignKey("question_banks.id", ondelete="CASCADE")),
    Column("question", Text, nullable=False),
    Column("question_type", String(50), nullable=False),  # 'multiple_choice', 'true_false', 'open_ended'
    
    # Answer storage - different formats for different types
    Column("correct_answer", Text, nullable=False),
    Column("answer_options", JSONB),  # For MCQ: ["option1", "option2", "option3", "option4"]
    
    # Metadata
    Column("category", String(100)),
    Column("subcategory", String(100)),  # For more granular categorization (e.g., 'smite' for open_ended)
    Column("difficulty", Integer, server_default=text("1")),  # 1=easy, 2=medium, 3=hard
    Column("tags", ARRAY(Text)),  # Array of tags for flexible categorization
    
    # Source tracking
    Column("source_id", String(255)),  # External ID from API or file
    Column("source_data", JSONB),  # Original data from source for reference
    
    # Statistics
    Column("times_asked", Integer, server_default=text("0")),
    Column("times_correct", Integer, server_default=text("0")),
    Column("avg_response_time", DECIMAL),
    
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP, server_default=func.current_timestamp()),
    
    # Constraints
    CheckConstraint(
        "question_type IN ('multiple_choice', 'true_false', 'open_ended')", 
        name='valid_question_type'
    ),
    CheckConstraint(
        "question_type != 'multiple_choice' OR (answer_options IS NOT NULL AND jsonb_array_length(answer_options) >= 2)",
        name='mcq_needs_options'
    ),
    CheckConstraint(
        "question_type != 'true_false' OR correct_answer IN ('true', 'false')",
        name='tf_valid_answer'
    )
)

sessions = Table(
    "sessions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("channel_id", Integer, ForeignKey("channels.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("session_type", String(50), server_default=text("'single'")),  # 'single', 'auto', 'tournament'
    Column("question_bank_id", Integer, ForeignKey("question_banks.id", ondelete="SET NULL")),
    Column("start_time", TIMESTAMP, server_default=func.current_timestamp()),
    Column("end_time", TIMESTAMP),
    Column("status", String(50), server_default=text("'active'")),  # 'active', 'completed', 'abandoned'
    Column("total_questions", Integer, server_default=text("0")),
    Column("total_correct", Integer, server_default=text("0")),
)

attempts = Table(
    "attempts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("session_id", Integer, ForeignKey("sessions.id", ondelete="CASCADE")),
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("channel_id", Integer, ForeignKey("channels.id", ondelete="CASCADE")),
    
    Column("user_answer", Text, nullable=False),
    Column("is_correct", Boolean, server_default=text("false")),
    Column("response_time_seconds", DECIMAL),  # Time taken to answer
    Column("answer_method", String(50)),  # 'letter_shortcut', 'full_text', 'fuzzy_match'
    
    Column("created_at", TIMESTAMP, server_default=func.current_timestamp()),
)

channel_users = Table(
    "channel_users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("channel_id", Integer, ForeignKey("channels.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    
    # Overall stats
    Column("first_seen", TIMESTAMP, server_default=func.current_timestamp()),
    Column("last_seen", TIMESTAMP, server_default=func.current_timestamp()),
    Column("total_questions", Integer, server_default=text("0")),
    Column("correct_answers", Integer, server_default=text("0")),
    
    # Streak tracking
    Column("current_streak", Integer, server_default=text("0")),
    Column("best_streak", Integer, server_default=text("0")),
    
    # Performance by question type
    Column("mcq_correct", Integer, server_default=text("0")),
    Column("mcq_total", Integer, server_default=text("0")),
    Column("tf_correct", Integer, server_default=text("0")),
    Column("tf_total", Integer, server_default=text("0")),
    Column("open_correct", Integer, server_default=text("0")),
    Column("open_total", Integer, server_default=text("0")),
    
    # Speed tracking
    Column("avg_response_time", DECIMAL),
    Column("fastest_correct_time", DECIMAL),
    
    # Engagement
    Column("sessions_participated", Integer, server_default=text("0")),
    Column("favorite_category", String(100)),
)

source_metadata = Table(
    "source_metadata",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bank_id", Integer, ForeignKey("question_banks.id", ondelete="CASCADE")),
    Column("source_identifier", String(255), nullable=False),  # file path, API endpoint, etc.
    Column("last_checked", TIMESTAMP, server_default=func.current_timestamp()),
    Column("last_modified", TIMESTAMP),
    Column("checksum", String(64)),  # For detecting file changes
    Column("record_count", Integer, server_default=text("0")),
    Column("status", String(50), server_default=text("'active'")),  # 'active', 'error', 'deprecated'
    Column("error_message", Text),
    Column("metadata", JSONB),  # Source-specific data like API tokens, rate limits, etc.
)

# Add indexes
Index('idx_questions_type_category', questions.c.question_type, questions.c.category)
Index('idx_questions_subcategory', questions.c.subcategory)
Index('idx_questions_bank_active', questions.c.bank_id)
Index('idx_questions_difficulty', questions.c.difficulty)
Index('idx_questions_tags', questions.c.tags, postgresql_using='gin')
Index('idx_questions_stats', questions.c.times_asked, questions.c.times_correct)

Index('idx_attempts_user_channel', attempts.c.user_id, attempts.c.channel_id)
Index('idx_attempts_correct_answers', attempts.c.is_correct)
Index('idx_attempts_session', attempts.c.session_id)
Index('idx_attempts_question', attempts.c.question_id)
Index('idx_attempts_time', attempts.c.created_at)

Index('idx_sessions_channel', sessions.c.channel_id)
Index('idx_sessions_status', sessions.c.status)
Index('idx_sessions_type', sessions.c.session_type)

Index('idx_channel_users_stats', channel_users.c.channel_id, channel_users.c.correct_answers.desc())
Index('idx_channel_users_streak', channel_users.c.channel_id, channel_users.c.best_streak.desc())
Index('idx_channels_twitch_id', channels.c.twitch_channel_id)

Index('idx_question_banks_source', question_banks.c.source_type, question_banks.c.is_active)
Index('idx_source_metadata_status', source_metadata.c.status, source_metadata.c.last_checked)

# Add unique constraint for channel_users
Index('uq_channel_users', channel_users.c.channel_id, channel_users.c.user_id, unique=True)