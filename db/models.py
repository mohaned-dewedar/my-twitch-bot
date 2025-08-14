from sqlalchemy import (
    Table, Column, Integer, String, Text, TIMESTAMP,
    ForeignKey, Boolean, JSON, MetaData, func , text
)

metadata = MetaData()

channels = Table(
    "channels",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")),
    Column("tier", Integer, server_default="0"),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("twitch_username", String(255), nullable=False, unique=True),
    Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")),
)

question_banks = Table(
    "question_banks",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
)

questions = Table(
    "questions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bank_id", Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True),
    Column("question", Text, nullable=False),
    Column("answer", Text, nullable=False),
    Column("options", JSON),
    Column("difficulty", Integer, server_default="1"),
    Column("category", String(100)),
    Column("type", String(50)),  # multiple_choice, true_false, etc.
    Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")),
)
sessions = Table(
    "sessions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("channel_id", Integer, ForeignKey("channels.id", ondelete="CASCADE")),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("start_time", TIMESTAMP, server_default=func.now()),
    Column("end_time", TIMESTAMP),
    Column("status", String(50), server_default="active"),  # active, completed, abandoned
)

attempts = Table(
    "attempts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("session_id", Integer, ForeignKey("sessions.id", ondelete="CASCADE")),
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE")),
    Column("user_answer", Text),
    Column("is_correct", Boolean, server_default="false"),
    Column("created_at", TIMESTAMP, server_default=func.now()),
)
