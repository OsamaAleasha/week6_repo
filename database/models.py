from sqlalchemy import MetaData, Table, Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from datetime import datetime

metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(100), unique=True, nullable=False),
    Column("email", String(120), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("last_login", DateTime, nullable=True),
)

analysis_history = Table(
    "analysis_history",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("input_text", Text, nullable=False),
    Column("sentiment_label", String(20), nullable=False),  # positive/negative/neutral
    Column("confidence_score", Float, nullable=False),
    Column("analysis_timestamp", DateTime, default=datetime.utcnow),
)

model_performance = Table(
    "model_performance",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("model_version", String(50), nullable=False),
    Column("accuracy", Float, nullable=False),
    Column("f1_score", Float, nullable=False),
    Column("training_date", DateTime, default=datetime.utcnow),
    Column("is_active", Boolean, default=False),
)