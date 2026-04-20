from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import select
from database.db import engine
from database.models import users

from dotenv import load_dotenv
import os
import bcrypt
import datetime

# ✅ JWT (correct usage for this library)
from jwt import JWT, jwk_from_dict

# -------------------------
# INIT
# -------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

SECRET_KEY = os.getenv("SECRET_KEY")

# JWT setup
jwt_instance = JWT()
key = jwk_from_dict({
    "k": SECRET_KEY,
    "kty": "oct"
})

# -------------------------
# JWT FUNCTIONS
# -------------------------
def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": int((datetime.datetime.utcnow() + datetime.timedelta(days=1)).timestamp())
    }
    return jwt_instance.encode(payload, key, alg="HS256")


def decode_token(token):
    try:
        data = jwt_instance.decode(token, key, do_time_check=True)
        return data["user_id"]
    except Exception:
        return None


def get_current_user():
    token = session.get("token")
    if not token:
        return None
    return decode_token(token)


# -------------------------
# AUTH ROUTES
# -------------------------

@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    with engine.connect() as conn:
        query = select(users).where(users.c.email == email)
        user = conn.execute(query).fetchone()

    if not user:
        return render_template("login.html", error="User not found")

    # 🔐 check password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return render_template("login.html", error="Invalid password")

    # 🔑 create token
    token = create_token(user.id)
    session["token"] = token

    return redirect(url_for("analyze"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # 🔐 hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        with engine.begin() as conn:
            result = conn.execute(
                users.insert().values(
                    username=username,
                    email=email,
                    password_hash=hashed_password
                )
            )
            user_id = result.inserted_primary_key[0]

    except Exception:
        return render_template("register.html", error="User already exists")

    # 🔑 create token
    token = create_token(user_id)
    session["token"] = token

    return redirect(url_for("analyze"))


@app.route("/logout")
def logout():
    session.pop("token", None)
    return redirect("/login")


# -------------------------
# PROTECTED ROUTES
# -------------------------

@app.route("/analyze", methods=["GET", "POST"])
def analyze():

    user_id = get_current_user()
    if not user_id:
        return redirect("/login")

    result = None

    if request.method == "POST":
        result = {
            "sentiment": "Positive",
            "confidence": "98.5%"
        }

    return render_template("analyze.html", result=result)


@app.route("/history")
def history():

    user_id = get_current_user()
    if not user_id:
        return redirect("/login")

    data = [
        {"input_text": "I love this!", "sentiment_label": "Positive", "confidence_score": 0.99, "analysis_timestamp": datetime.datetime.now()},
        {"input_text": "This is terrible.", "sentiment_label": "Negative", "confidence_score": 0.85, "analysis_timestamp": datetime.datetime.now()}
    ]

    return render_template("history.html", history=data)


@app.route("/profile")
def profile():

    user_id = get_current_user()
    if not user_id:
        return redirect("/login")

    user_data = {
        "username": "CodingPro",
        "email": "hello@example.com",
        "joined": "January 2026"
    }

    stats_data = {
        "total": 42,
        "avg_conf": 88.5,
        "top_sentiment": "Positive"
    }

    recent = [
        {"text": "The service was amazing and fast.", "label": "Positive"},
        {"text": "I hated the long wait times.", "label": "Negative"},
        {"text": "It was an average experience.", "label": "Neutral"}
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats_data,
        recent_activity=recent
    )


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)