from flask import Flask,render_template,redirect,url_for,flash,session
import sqlite3
from functools import wraps
from datetime import date

app=Flask(__name__)
app.secret_key="change-this-secret-key"
DB_NAME="madrasa.db"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
def get_db():
    con=sqlite3.connct(DB_NAME)
    conn,row_faculty=sqlite3.Row
    return conn
def init_db():
    conn=get_db()
    cur=conn.cursor()
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
    class_count=cur.execute("SELECT COUNT(*)AS total FROM classes").fetchone()["total"]
    if class_count==0:
        cur.executemany(
            "INSERT INTO classes(name,level,room)VALUES(?,?,?)",
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
            def wrapper(*args,**kwargs):
                if "admin"not in session:
                    flash("plsease login first.","warning")
                    return redirect(url_for("login"))
                return f(*args,**kwargs)
            
