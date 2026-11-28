from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db_connection
from ai_service import generate_learning_roadmap
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "evolve-development-key")

init_db()


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# USER REGISTRATION
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


# USER LOGIN
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


# USER DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    skills = conn.execute(
        "SELECT * FROM skills WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    # Get AI learning tasks for each skill
    skill_tasks = {}

    for skill in skills:

        tasks = conn.execute(
            """
            SELECT * FROM learning_tasks
            WHERE skill_id = ?
            ORDER BY level ASC, id ASC
            """,
            (skill["id"],)
        ).fetchall()

        skill_tasks[skill["id"]] = tasks

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        skills=skills,
        skill_tasks=skill_tasks
    )


# USER LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# CREATE NEW SKILL + AI ROADMAP
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

        conn = None

        try:

            # STEP 1: Generate AI Roadmap

            roadmap = generate_learning_roadmap(
                skill_name,
                current_level,
                target_level,
                motivation
            )

            # STEP 2: Validate AI Response

            if not isinstance(roadmap, dict) or not isinstance(
                roadmap.get("levels"), list
            ):
                raise ValueError("Invalid roadmap format")

            # STEP 3: Save Skill in Database

            conn = get_db_connection()

            cursor = conn.execute("""
                INSERT INTO skills
                (user_id, skill_name, current_level,
                target_level, deadline, motivation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                skill_name,
                current_level,
                target_level,
                deadline,
                motivation
            ))

            skill_id = cursor.lastrowid

            # STEP 4: Save AI Generated Tasks

            for level_data in roadmap["levels"]:

                level_number = level_data["level"]
                level_title = level_data["title"]

                for task in level_data["tasks"]:

                    conn.execute("""
                        INSERT INTO learning_tasks
                        (skill_id, title, description, level)
                        VALUES (?, ?, ?, ?)
                    """, (
                        skill_id,
                        f"{level_title}: {task['title']}",
                        task["description"],
                        level_number
                    ))

            # STEP 5: Save Changes

            conn.commit()
            conn.close()
            conn = None

            return redirect(url_for("dashboard"))

        except Exception as e:

            print("AI Roadmap Error:", e)

            if conn:
                conn.rollback()
                conn.close()

            return render_template(
                "new_skill.html",
                message="Roadmap generation failed. Please try again."
            )

    return render_template("new_skill.html")


# RUN APPLICATION
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )