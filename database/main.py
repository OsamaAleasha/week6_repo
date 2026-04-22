from database.db import engine
from database.models import metadata, users, analysis_history, model_performance
from sqlalchemy import insert, select, delete, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

metadata.create_all(engine)

# -------------------------
# User Functions
# -------------------------

def get_user_by_email(email):
    with engine.connect() as conn:
        return conn.execute(
            select(users).where(users.c.email == email)
        ).fetchone()


def get_user_by_id(user_id):
    with engine.connect() as conn:
        return conn.execute(
            select(users).where(users.c.id == user_id)
        ).fetchone()


def create_user(username, email, password_hash):
    with engine.begin() as conn:
        result = conn.execute(
            users.insert().values(
                username=username,
                email=email,
                password_hash=password_hash
            )
        )
        return result.inserted_primary_key[0]
    

# -------------------------
# Analysis Functions
# -------------------------

def add_analysis(user_id, text, sentiment, confidence):
    with engine.begin() as conn:
        conn.execute(
            analysis_history.insert().values(
                user_id=user_id,
                input_text=text,
                sentiment_label=sentiment,
                confidence_score=confidence
            )
        )


def get_user_history(user_id):
    with engine.connect() as conn:
        return conn.execute(
            select(analysis_history)
            .where(analysis_history.c.user_id == user_id)
            .order_by(analysis_history.c.analysis_timestamp.desc())
        ).fetchall()


def get_user_analytics(user_id):
    with engine.connect() as conn:
        return conn.execute(
            select(analysis_history)
            .where(analysis_history.c.user_id == user_id)
        ).fetchall()