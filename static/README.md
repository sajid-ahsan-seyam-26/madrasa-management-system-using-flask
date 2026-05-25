# Madrasa Management System - Flask + SQLite

A beginner-friendly Madrasa Management System built with Flask and SQLite.

## Features

- Admin login
- Dashboard with totals
- Student management
- Teacher management
- Class management
- Attendance management
- Fee management
- Exam marks management
- Simple reports
- Clean responsive UI

## Default Login

Username: `admin`  
Password: `admin123`

## How to Run

1. Open the project folder in VS Code.

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

4. Install Flask:

```bash
pip install -r requirements.txt
```

5. Run the project:

```bash
python app.py
```

6. Open in browser:

```text
http://127.0.0.1:5000
```

## Database

The SQLite database file `madrasa.db` will be created automatically when you run the app.

## Project Structure

```text
madrasa_management_system/
├── app.py
├── requirements.txt
├── README.md
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── students.html
    ├── student_form.html
    ├── teachers.html
    ├── teacher_form.html
    ├── classes.html
    ├── class_form.html
    ├── attendance.html
    ├── fees.html
    ├── fee_form.html
    ├── marks.html
    ├── mark_form.html
    └── reports.html
```
