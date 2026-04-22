from flask import Flask, render_template, request, redirect, url_for, jsonify
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

# JWT HELPER FUNCTIONS

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
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    return decode_token(token)

# PAGE ROUTES (Serve HTML)
@app.route("/")
def home():
    return redirect("/login")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/analyze")
def analyze_page():
    return render_template("analyze.html")

@app.route("/history-page")
def history_page():
    return render_template("history.html")

@app.route("/profile-page")
def profile_page():
    return render_template("profile.html")

@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")

# API ROUTES (Handle Data & Auth)

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "Invalid password"}), 401

    token = create_token(user.id)
    return jsonify({"token": token, "redirect": "/analyze"})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        user_id = create_user(username, email, hashed_password)
    except Exception:
        return jsonify({"error": "User already exists"}), 400

    token = create_token(user_id)
    return jsonify({"token": token, "redirect": "/analyze"})

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    text = data.get("text", "")

    # Sentiment Logic
    positive_words = ["love", "great", "amazing", "good", "excellent", "awesome"]
    negative_words = ["hate", "bad", "terrible", "awful", "worst", "horrible"]
    text_lower = text.lower()

    if any(word in text_lower for word in positive_words):
        sentiment, confidence = "Positive", 0.95
    elif any(word in text_lower for word in negative_words):
        sentiment, confidence = "Negative", 0.95
    else:
        sentiment, confidence = "Neutral", 0.70

    add_analysis(user_id, text, sentiment, confidence)

    return jsonify({
        "sentiment": sentiment,
        "confidence": f"{confidence * 100:.2f}%"
    })

@app.route("/api/history")
def api_history():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    rows = get_user_history(user_id)
    data = [
        {
            "input_text": row.input_text,
            "sentiment_label": row.sentiment_label,
            "confidence_score": round(row.confidence_score * 100, 2),
            "analysis_timestamp": row.analysis_timestamp
        }
        for row in rows
    ]
    return jsonify(data)

@app.route("/api/profile")
def api_profile():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    user = get_user_by_id(user_id)
    history = get_user_analytics(user_id)
    total = len(history)

    if total > 0:
        avg_conf = round(sum(h.confidence_score for h in history) / total * 100, 2)
        sentiments = [h.sentiment_label for h in history]
        top_sentiment = max(set(sentiments), key=sentiments.count)
    else:
        avg_conf, top_sentiment = 0, "N/A"

    recent = [{"text": h.input_text, "label": h.sentiment_label} for h in history[-3:]]

    return jsonify({
        "user": {
            "username": user.username,
            "email": user.email,
            "joined": user.created_at.strftime("%B %Y")
        },
        "stats": {
            "total": total,
            "avg_conf": avg_conf,
            "top_sentiment": top_sentiment
        },
        "recent_activity": recent
    })

if __name__ == "__main__":
    app.run(debug=True)