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


@app.route("/classes/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_class(id):
    conn = get_db()
    class_item = conn.execute("SELECT * FROM classes WHERE id = ?", (id,)).fetchone()

    if not class_item:
        conn.close()
        flash("Class not found.", "danger")
        return redirect(url_for("classes"))

    if request.method == "POST":
        name = request.form.get("name")
        level = request.form.get("level")
        room = request.form.get("room")

        conn.execute("UPDATE classes SET name = ?, level = ?, room = ? WHERE id = ?", (name, level, room, id))
        conn.commit()
        conn.close()

        flash("Class updated successfully.", "success")
        return redirect(url_for("classes"))

    conn.close()
    return render_template("class_form.html", title="Edit Class", class_item=class_item)


@app.route("/classes/delete/<int:id>", methods=["POST"])
@login_required
def delete_class(id):
    conn = get_db()
    conn.execute("DELETE FROM classes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Class deleted successfully.", "info")
    return redirect(url_for("classes"))


# ---------------- Students ----------------

@app.route("/students")
@login_required
def students():
    search = request.args.get("search", "").strip()
    conn = get_db()

    if search:
        rows = conn.execute("""
            SELECT students.*, classes.name AS class_name
            FROM students
            LEFT JOIN classes ON students.class_id = classes.id
            WHERE students.name LIKE ? OR students.admission_no LIKE ? OR students.guardian_phone LIKE ?
            ORDER BY students.id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("""
            SELECT students.*, classes.name AS class_name
            FROM students
            LEFT JOIN classes ON students.class_id = classes.id
            ORDER BY students.id DESC
        """).fetchall()

    conn.close()
    return render_template("students.html", students=rows, search=search)


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    conn = get_db()
    class_list = conn.execute("SELECT * FROM classes ORDER BY name ASC").fetchall()

    if request.method == "POST":
        data = (
            request.form.get("admission_no"),
            request.form.get("name"),
            request.form.get("father_name"),
            request.form.get("guardian_phone"),
            request.form.get("address"),
            request.form.get("class_id") or None,
            request.form.get("status"),
            request.form.get("admission_date"),
        )

        try:
            conn.execute("""
                INSERT INTO students
                (admission_no, name, father_name, guardian_phone, address, class_id, status, admission_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            flash("Student added successfully.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            flash("Admission number already exists.", "danger")

    conn.close()
    return render_template("student_form.html", title="Add Student", student=None, classes=class_list)


@app.route("/students/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (id,)).fetchone()
    class_list = conn.execute("SELECT * FROM classes ORDER BY name ASC").fetchall()

    if not student:
        conn.close()
        flash("Student not found.", "danger")
        return redirect(url_for("students"))

    if request.method == "POST":
        data = (
            request.form.get("admission_no"),
            request.form.get("name"),
            request.form.get("father_name"),
            request.form.get("guardian_phone"),
            request.form.get("address"),
            request.form.get("class_id") or None,
            request.form.get("status"),
            request.form.get("admission_date"),
            id,
        )

        try:
            conn.execute("""
                UPDATE students
                SET admission_no = ?, name = ?, father_name = ?, guardian_phone = ?,
                    address = ?, class_id = ?, status = ?, admission_date = ?
                WHERE id = ?
            """, data)
            conn.commit()
            flash("Student updated successfully.", "success")
            return redirect(url_for("students"))
        except sqlite3.IntegrityError:
            flash("Admission number already exists.", "danger")

    conn.close()
    return render_template("student_form.html", title="Edit Student", student=student, classes=class_list)


@app.route("/students/delete/<int:id>", methods=["POST"])
@login_required
def delete_student(id):
    conn = get_db()
    conn.execute("DELETE FROM attendance WHERE student_id = ?", (id,))
    conn.execute("DELETE FROM fees WHERE student_id = ?", (id,))
    conn.execute("DELETE FROM marks WHERE student_id = ?", (id,))
    conn.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Student deleted successfully.", "info")
    return redirect(url_for("students"))


# ---------------- Teachers ----------------

@app.route("/teachers")
@login_required
def teachers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM teachers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("teachers.html", teachers=rows)


@app.route("/teachers/add", methods=["GET", "POST"])
@login_required
def add_teacher():
    if request.method == "POST":
        data = (
            request.form.get("name"),
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("subject"),
            request.form.get("join_date"),
        )

        conn = get_db()
        conn.execute("INSERT INTO teachers (name, phone, email, subject, join_date) VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()

        flash("Teacher added successfully.", "success")
        return redirect(url_for("teachers"))

    return render_template("teacher_form.html", title="Add Teacher", teacher=None)


@app.route("/teachers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_teacher(id):
    conn = get_db()
    teacher = conn.execute("SELECT * FROM teachers WHERE id = ?", (id,)).fetchone()

    if not teacher:
        conn.close()
        flash("Teacher not found.", "danger")
        return redirect(url_for("teachers"))

    if request.method == "POST":
        data = (
            request.form.get("name"),
            request.form.get("phone"),
            request.form.get("email"),
            request.form.get("subject"),
            request.form.get("join_date"),
            id,
        )

        conn.execute("UPDATE teachers SET name = ?, phone = ?, email = ?, subject = ?, join_date = ? WHERE id = ?", data)
        conn.commit()
        conn.close()

        flash("Teacher updated successfully.", "success")
        return redirect(url_for("teachers"))

    conn.close()
    return render_template("teacher_form.html", title="Edit Teacher", teacher=teacher)


@app.route("/teachers/delete/<int:id>", methods=["POST"])
@login_required
def delete_teacher(id):
    conn = get_db()
    conn.execute("DELETE FROM teachers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Teacher deleted successfully.", "info")
    return redirect(url_for("teachers"))


# ---------------- Attendance ----------------

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    conn = get_db()
    class_list = conn.execute("SELECT * FROM classes ORDER BY name ASC").fetchall()

    selected_date = request.values.get("date") or str(date.today())
    selected_class = request.values.get("class_id") or ""

    if request.method == "POST":
        student_ids = request.form.getlist("student_ids")

        for student_id in student_ids:
            status = request.form.get(f"status_{student_id}", "Absent")
            remarks = request.form.get(f"remarks_{student_id}", "")

            conn.execute("DELETE FROM attendance WHERE student_id = ? AND date = ?", (student_id, selected_date))
            conn.execute("""
                INSERT INTO attendance (student_id, date, status, remarks)
                VALUES (?, ?, ?, ?)
            """, (student_id, selected_date, status, remarks))

        conn.commit()
        flash("Attendance saved successfully.", "success")
        return redirect(url_for("attendance", date=selected_date, class_id=selected_class))

    students_query = """
        SELECT students.*, classes.name AS class_name
        FROM students
        LEFT JOIN classes ON students.class_id = classes.id
        WHERE students.status = 'Active'
    """
    params = []

    if selected_class:
        students_query += " AND students.class_id = ?"
        params.append(selected_class)

    students_query += " ORDER BY students.name ASC"
    student_list = conn.execute(students_query, params).fetchall()

    existing = conn.execute("SELECT * FROM attendance WHERE date = ?", (selected_date,)).fetchall()
    attendance_map = {str(row["student_id"]): row for row in existing}

    conn.close()
    return render_template(
        "attendance.html",
        classes=class_list,
        students=student_list,
        attendance_map=attendance_map,
        selected_date=selected_date,
        selected_class=selected_class,
    )


# ---------------- Fees ----------------

@app.route("/fees")
@login_required
def fees():
    conn = get_db()
    rows = conn.execute("""
        SELECT fees.*, students.name AS student_name, students.admission_no
        FROM fees
        JOIN students ON fees.student_id = students.id
        ORDER BY fees.id DESC
    """).fetchall()
    conn.close()
    return render_template("fees.html", fees=rows)


@app.route("/fees/add", methods=["GET", "POST"])
@login_required
def add_fee():
    conn = get_db()
    students_list = conn.execute("SELECT * FROM students ORDER BY name ASC").fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id")
        month = request.form.get("month")
        amount = float(request.form.get("amount") or 0)
        paid_amount = float(request.form.get("paid_amount") or 0)
        status = "Paid" if paid_amount >= amount else "Due"

        conn.execute("""
            INSERT INTO fees (student_id, month, amount, paid_amount, status, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            month,
            amount,
            paid_amount,
            status,
            request.form.get("due_date"),
            str(date.today()),
        ))

        conn.commit()
        conn.close()
        flash("Fee record added successfully.", "success")
        return redirect(url_for("fees"))

    conn.close()
    return render_template("fee_form.html", students=students_list)


@app.route("/fees/pay/<int:id>", methods=["POST"])
@login_required
def pay_fee(id):
    conn = get_db()
    fee = conn.execute("SELECT * FROM fees WHERE id = ?", (id,)).fetchone()

    if fee:
        conn.execute("UPDATE fees SET paid_amount = amount, status = 'Paid' WHERE id = ?", (id,))
        conn.commit()
        flash("Fee marked as paid.", "success")
    else:
        flash("Fee record not found.", "danger")

    conn.close()
    return redirect(url_for("fees"))


@app.route("/fees/delete/<int:id>", methods=["POST"])
@login_required
def delete_fee(id):
    conn = get_db()
    conn.execute("DELETE FROM fees WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Fee record deleted.", "info")
    return redirect(url_for("fees"))


# ---------------- Marks ----------------

@app.route("/marks")
@login_required
def marks():
    conn = get_db()
    rows = conn.execute("""
        SELECT marks.*, students.name AS student_name, students.admission_no
        FROM marks
        JOIN students ON marks.student_id = students.id
        ORDER BY marks.id DESC
    """).fetchall()
    conn.close()
    return render_template("marks.html", marks=rows)


@app.route("/marks/add", methods=["GET", "POST"])
@login_required
def add_mark():
    conn = get_db()
    students_list = conn.execute("SELECT * FROM students ORDER BY name ASC").fetchall()

    if request.method == "POST":
        conn.execute("""
            INSERT INTO marks (student_id, subject, exam_name, marks, total_marks, exam_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form.get("student_id"),
            request.form.get("subject"),
            request.form.get("exam_name"),
            request.form.get("marks"),
            request.form.get("total_marks"),
            request.form.get("exam_date"),
        ))

        conn.commit()
        conn.close()
        flash("Exam mark added successfully.", "success")
        return redirect(url_for("marks"))

    conn.close()
    return render_template("mark_form.html", students=students_list)


@app.route("/marks/delete/<int:id>", methods=["POST"])
@login_required
def delete_mark(id):
    conn = get_db()
    conn.execute("DELETE FROM marks WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Mark record deleted.", "info")
    return redirect(url_for("marks"))


# ---------------- Reports ----------------

@app.route("/reports")
@login_required
def reports():
    conn = get_db()

    attendance_summary = conn.execute("""
        SELECT students.name AS student_name,
               students.admission_no,
               SUM(CASE WHEN attendance.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
               SUM(CASE WHEN attendance.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
               SUM(CASE WHEN attendance.status = 'Late' THEN 1 ELSE 0 END) AS late_count
        FROM students
        LEFT JOIN attendance ON students.id = attendance.student_id
        GROUP BY students.id
        ORDER BY students.name ASC
    """).fetchall()

    due_fees = conn.execute("""
        SELECT students.name AS student_name,
               students.admission_no,
               SUM(fees.amount - fees.paid_amount) AS due_amount
        FROM fees
        JOIN students ON fees.student_id = students.id
        WHERE fees.status != 'Paid'
        GROUP BY students.id
        ORDER BY due_amount DESC
    """).fetchall()

    conn.close()
    return render_template("reports.html", attendance_summary=attendance_summary, due_fees=due_fees)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
