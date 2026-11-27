from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "evolve-development-key")

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            return render_template(
                "register.html",
                message="Email already registered!"
            )

        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return render_template(
            "register.html",
            message="Account created successfully!"
        )

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            message="Invalid email or password!"
        )

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    skills = conn.execute(
        "SELECT * FROM skills WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        skills=skills
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/new-skill", methods=["GET", "POST"])
def new_skill():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        skill_name = request.form["skill_name"]
        current_level = request.form["current_level"]
        target_level = request.form["target_level"]
        deadline = request.form.get("deadline")
        motivation = request.form.get("motivation")

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO skills
            (user_id, skill_name, current_level, target_level, deadline, motivation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            skill_name,
            current_level,
            target_level,
            deadline,
            motivation
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("new_skill.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)