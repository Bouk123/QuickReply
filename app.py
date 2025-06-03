from flask import Flask , render_template, request, redirect, render_template_string, session, url_for
import openai
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import json

USERS="users.json"
def load_users():
    if not os.path.exists(USERS):
        with open(USERS, "w") as f:
            json.dump([], f)
    with open(USERS, "r") as f:
        return json.load(f)
def save_users(users):
    with open(USERS, "w") as f:
        json.dump(users,f,indent=4)

load_dotenv()
openai.api_key =os.getenv("OPENAI_API_KEY")

app =Flask(__name__)
app.secret_key = "your_very_secret_key_here"

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("user"):
        return redirect(url_for('login'))
    ai_reply = None
    if request.method=="POST":
        review=request.form.get("review")
        platform=request.form.get("platform")
        tone=request.form.get("tone")

        prompt =f"""
        You are a proffesional and polite host on {platform}.
        Respond to this review in a {tone} tone :

        "{review}"
        Keep it short, polite and empathetic, also detect the languange and answer in that language. keep it short and correct
        """
        response=openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You help hospitality businesses reply to reviews."},
                {"role":"user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        session["ai_reply"]=response["choices"][0]["message"]["content"]
        return redirect(url_for("index"))
    ai_reply=session.pop("ai_reply", None)
    return render_template("index.html",ai_reply=ai_reply)

@app.route("/register", methods=["GET", "POST"])
def register():
   

    message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        users = load_users()

        # Validation checks
        if not username:
            message = "Username is required."
        elif len(password) < 6:
            message = "Password must be at least 6 characters."
        elif password != confirm:
            message = "Passwords do not match."
        elif any(u["username"] == username for u in users):
            message = "Username already exists."
        else:
            hashed_pw = generate_password_hash(password)
            users.append({"username": username, "password": hashed_pw})
            save_users(users)
            session.pop("user", None)
            session["user"] = username
            return redirect(url_for("index"))  # Redirect to index, not login

    return render_template("register.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("index"))

    message = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        users = load_users()
        user = next((u for u in users if u["username"] == username), None)

        if not user:
            message = "Username not found."
        elif not check_password_hash(user["password"], password):
            message = "Incorrect password."
        else:
            session.pop("user", None)
            session["user"] = username
            return redirect(url_for("index"))

    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))
