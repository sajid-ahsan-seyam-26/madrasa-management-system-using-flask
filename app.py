from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB_NAME = "madrasa.db"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level TEXT,
            room TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT UNIQUE,
            name TEXT NOT NULL,
            father_name TEXT,
            guardian_phone TEXT,
            address TEXT,
            class_id INTEGER,
            status TEXT DEFAULT 'Active',
            admission_date TEXT,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            subject TEXT,
            join_date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            remarks TEXT,
            UNIQUE(student_id, date),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Due',
            due_date TEXT,
            created_at TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            exam_name TEXT NOT NULL,
            marks REAL NOT NULL,
            total_marks REAL NOT NULL,
            exam_date TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    # Add demo classes only if database is empty
    class_count = cur.execute("SELECT COUNT(*) AS total FROM classes").fetchone()["total"]
    if class_count == 0:
        cur.executemany(
            "INSERT INTO classes (name, level, room) VALUES (?, ?, ?)",
            [
                ("Nazera", "Beginner", "Room 101"),
                ("Hifz", "Intermediate", "Room 102"),
                ("Alim", "Advanced", "Room 201"),
            ],
        )

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    if "admin" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = username
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    stats = {
        "students": conn.execute("SELECT COUNT(*) AS total FROM students").fetchone()["total"],
        "teachers": conn.execute("SELECT COUNT(*) AS total FROM teachers").fetchone()["total"],
        "classes": conn.execute("SELECT COUNT(*) AS total FROM classes").fetchone()["total"],
        "due_fees": conn.execute("SELECT COALESCE(SUM(amount - paid_amount), 0) AS total FROM fees WHERE status != 'Paid'").fetchone()["total"],
        "today_present": conn.execute("SELECT COUNT(*) AS total FROM attendance WHERE date = ? AND status = 'Present'", (str(date.today()),)).fetchone()["total"],
        "today_absent": conn.execute("SELECT COUNT(*) AS total FROM attendance WHERE date = ? AND status = 'Absent'", (str(date.today()),)).fetchone()["total"],
    }

    recent_students = conn.execute("""
        SELECT students.*, classes.name AS class_name
        FROM students
        LEFT JOIN classes ON students.class_id = classes.id
        ORDER BY students.id DESC
        LIMIT 5
    """).fetchall()
    conn.close()

    return render_template("dashboard.html", stats=stats, recent_students=recent_students)


# ---------------- Classes ----------------

@app.route("/classes")
@login_required
def classes():
    conn = get_db()
    rows = conn.execute("SELECT * FROM classes ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("classes.html", classes=rows)


@app.route("/classes/add", methods=["GET", "POST"])
@login_required
def add_class():
    if request.method == "POST":
        name = request.form.get("name")
        level = request.form.get("level")
        room = request.form.get("room")

        conn = get_db()
        conn.execute("INSERT INTO classes (name, level, room) VALUES (?, ?, ?)", (name, level, room))
        conn.commit()
        conn.close()

        flash("Class added successfully.", "success")
        return redirect(url_for("classes"))

    return render_template("class_form.html", title="Add Class", class_item=None)


            
