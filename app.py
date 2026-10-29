from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"
DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(skill_id) REFERENCES skills(id),
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id)
    )""")
    # Messages persist in SQLite so conversations remain after restarting the app.
    conn.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        receiver_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        sent_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

def login_required():
    return "user_id" in session

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name and email. Password must be at least 6 characters.")
            return render_template("register.html")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                         (name, email, generate_password_hash(password)))
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))
    conn = get_db()
    skills = conn.execute("SELECT * FROM skills WHERE user_id = ?", (session["user_id"],)).fetchall()
    requests_received = conn.execute("""
        SELECT requests.*, skills.skill_name, users.name AS sender_name
        FROM requests JOIN skills ON requests.skill_id = skills.id
        JOIN users ON requests.sender_id = users.id
        WHERE requests.receiver_id = ? ORDER BY requests.id DESC
    """, (session["user_id"],)).fetchall()
    conn.close()
    return render_template("dashboard.html", skills=skills, requests=requests_received)

@app.route("/add_skill", methods=["GET", "POST"])
def add_skill():
    if not login_required():
        return redirect(url_for("login"))
    if request.method == "POST":
        skill_name = request.form.get("skill_name", "").strip()
        description = request.form.get("description", "").strip()
        skill_type = request.form.get("type", "I Can Teach")
        if skill_name:
            conn = get_db()
            conn.execute("INSERT INTO skills (user_id,skill_name,description,type) VALUES (?,?,?,?)",
                         (session["user_id"], skill_name, description, skill_type))
            conn.commit()
            conn.close()
            flash("Skill added successfully.")
            return redirect(url_for("dashboard"))
    return render_template("add_skill.html")

@app.route("/skills")
def skills():
    if not login_required():
        return redirect(url_for("login"))
    search = request.args.get("search", "").strip()
    conn = get_db()
    found_skills = conn.execute("""
        SELECT skills.*, users.name
        FROM skills JOIN users ON skills.user_id = users.id
        WHERE skills.skill_name LIKE ? AND skills.user_id != ?
        ORDER BY skills.id DESC
    """, ("%" + search + "%", session["user_id"])).fetchall()
    conn.close()
    return render_template("skills.html", skills=found_skills, search=search)

@app.route("/request_skill/<int:skill_id>", methods=["POST"])
def request_skill(skill_id):
    if not login_required():
        return redirect(url_for("login"))
    conn = get_db()
    skill = conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,)).fetchone()
    if skill and skill["user_id"] != session["user_id"]:
        conn.execute("INSERT INTO requests (skill_id,sender_id,receiver_id) VALUES (?,?,?)",
                     (skill_id, session["user_id"], skill["user_id"]))
        conn.commit()
        flash("Skill exchange request sent.")
    else:
        flash("You cannot request your own skill.")
    conn.close()
    return redirect(url_for("skills"))

@app.route("/request/<int:request_id>/<action>", methods=["POST"])
def update_request(request_id, action):
    if not login_required():
        return redirect(url_for("login"))
    if action not in ["Accepted", "Rejected"]:
        return redirect(url_for("dashboard"))
    conn = get_db()
    conn.execute("UPDATE requests SET status = ? WHERE id = ? AND receiver_id = ?",
                 (action, request_id, session["user_id"]))
    conn.commit()
    conn.close()
    flash(f"Request {action.lower()}.")
    return redirect(url_for("dashboard"))

@app.route("/chats")
def chats():
    if not login_required():
        return redirect(url_for("login"))
    uid = session["user_id"]
    conn = get_db()
    people = conn.execute("""
        SELECT u.id, u.name,
          (SELECT message FROM messages m
           WHERE (m.sender_id = u.id AND m.receiver_id = ?) OR
                 (m.sender_id = ? AND m.receiver_id = u.id)
           ORDER BY m.id DESC LIMIT 1) AS last_message,
          (SELECT sent_at FROM messages m
           WHERE (m.sender_id = u.id AND m.receiver_id = ?) OR
                 (m.sender_id = ? AND m.receiver_id = u.id)
           ORDER BY m.id DESC LIMIT 1) AS last_time
        FROM users u WHERE u.id != ?
        ORDER BY last_time DESC, u.name COLLATE NOCASE
    """, (uid, uid, uid, uid, uid)).fetchall()
    conn.close()
    return render_template("chats.html", people=people)

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
def chat(user_id):
    if not login_required():
        return redirect(url_for("login"))
    current_id = session["user_id"]
    if user_id == current_id:
        return redirect(url_for("chats"))
    conn = get_db()
    other = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not other:
        conn.close()
        flash("User not found.")
        return redirect(url_for("chats"))
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message and len(message) <= 2000:
            conn.execute("INSERT INTO messages (sender_id,receiver_id,message) VALUES (?,?,?)",
                         (current_id, user_id, message))
            conn.commit()
        elif len(message) > 2000:
            flash("Message is too long. Please keep it under 2000 characters.")
        conn.close()
        return redirect(url_for("chat", user_id=user_id))
    messages = conn.execute("""
        SELECT messages.*, users.name AS sender_name
        FROM messages JOIN users ON messages.sender_id = users.id
        WHERE (sender_id = ? AND receiver_id = ?) OR
              (sender_id = ? AND receiver_id = ?)
        ORDER BY messages.id ASC
    """, (current_id, user_id, user_id, current_id)).fetchall()
    conn.close()
    return render_template("chat.html", other=other, messages=messages)

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
