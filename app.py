from flask import Flask, render_template, request, redirect, url_for, session
from sqlalchemy import select
from database.db import engine
from database.models import users, analysis_history
from database.main import *

from dotenv import load_dotenv
import os
import bcrypt
import datetime

from jwt import JWT, jwk_from_dict

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


# JWT FUNCTIONS
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


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():

    # show login page
    if request.method == "GET":
        return render_template("login.html")

    # get form data
    email = request.form.get("email")
    password = request.form.get("password")

    # find user in DB
    user = get_user_by_email(email)

    if not user:
        return render_template("login.html", error="User not found")

    # check password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return render_template("login.html", error="Invalid password")

    # create session token
    token = create_token(user.id)
    session["token"] = token

    return redirect(url_for("analyze"))


@app.route("/register", methods=["GET", "POST"])
def register():

    # show register page
    if request.method == "GET":
        return render_template("register.html")

    # get form data
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # hash password before storing
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        # create new user in DB
        user_id = create_user(username, email, hashed_password)

    except Exception:
        return render_template("register.html", error="User already exists")

    # create session token
    token = create_token(user_id)
    session["token"] = token

    return redirect(url_for("analyze"))


@app.route("/logout")
def logout():
    session.pop("token", None)
    return redirect("/login")


@app.route("/analyze", methods=["GET", "POST"])
def analyze():

    # check login
    user_id = get_current_user()
    if not user_id:
        return redirect("/login")

    result = None

    # when form submitted
    if request.method == "POST":
        text = request.form.get("text")

        ###############################################################################
        # Simple sentiment logic (placeholder)
        positive_words = ["love", "great", "amazing", "good", "excellent", "awesome"]
        negative_words = ["hate", "bad", "terrible", "awful", "worst", "horrible"]

        text_lower = text.lower()

        if any(word in text_lower for word in positive_words):
            sentiment = "Positive"
            confidence = 0.9
        elif any(word in text_lower for word in negative_words):
            sentiment = "Negative"
            confidence = 0.9
        else:
            sentiment = "Neutral"
            confidence = 0.75
        ###############################################################################

        # result shown in UI
        result = {
            "sentiment": sentiment,
            "confidence": f"{confidence * 100:.2f}%"
        }

        # save analysis to database
        add_analysis(user_id, text, sentiment, confidence)

    return render_template("analyze.html", result=result)


@app.route("/history")
def history():

    # check login
    user_id = get_current_user()
    if not user_id:
        return redirect("/login")
    
    # get user history from DB
    rows = get_user_history(user_id)

    # format data for template
    data = [
        {
            "input_text": row.input_text,
            "sentiment_label": row.sentiment_label,
            "confidence_score": round(row.confidence_score * 100, 2),
            "analysis_timestamp": row.analysis_timestamp
        }
        for row in rows
    ]

    return render_template("history.html", history=data)


@app.route("/profile")
def profile():

    # check login
    user_id = get_current_user()
    if not user_id:
        return redirect("/login")
    
    # get user info + history
    user = get_user_by_id(user_id)
    history = get_user_analytics(user_id)


    # get total analyses
    total = len(history)

    # calculate stats
    if total > 0:
        avg_conf = round(
            sum(h.confidence_score for h in history) / total * 100, 2
        )

        sentiments = [h.sentiment_label for h in history]
        top_sentiment = max(set(sentiments), key=sentiments.count)

    else:
        avg_conf = 0
        top_sentiment = "N/A"

    # last 3 activities
    recent = [
        {"text": h.input_text, "label": h.sentiment_label}
        for h in history[-3:]
    ]

    # user info for template
    user_data = {
        "username": user.username,
        "email": user.email,
        "joined": user.created_at.strftime("%B %Y")
    }

    stats_data = {
        "total": total,
        "avg_conf": avg_conf,
        "top_sentiment": top_sentiment
    }

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats_data,
        recent_activity=recent
    )


@app.route("/analytics")
def analytics():

    # check login
    user_id = get_current_user()
    if not user_id:
        return redirect("/login")
    
    # get all user data
    rows = get_user_analytics(user_id)

    # get total analyses
    total = len(rows)

    # sentiment counts
    positive = sum(1 for r in rows if r.sentiment_label == "Positive")
    negative = sum(1 for r in rows if r.sentiment_label == "Negative")
    neutral = sum(1 for r in rows if r.sentiment_label == "Neutral")

    # average confidence
    avg_conf = (
        sum(r.confidence_score for r in rows) / total
        if total > 0 else 0
    )

    # final analytics data
    data = {
        "total_analyses": total,
        "sentiment_distribution": {
            "positive": positive,
            "neutral": neutral,
            "negative": negative
        },
        "average_confidence": round(avg_conf, 2)
    }

    return render_template("analytics.html", data=data)



if __name__ == "__main__":
    app.run(debug=True)