import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "messmind.db")

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            display_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waste_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            student_id TEXT NOT NULL,
            meal TEXT NOT NULL,
            weight REAL NOT NULL,
            record_date TEXT NOT NULL,
            record_time TEXT NOT NULL,
            flag TEXT NOT NULL
        )
    """)

    # Seed default users
    cursor.executemany("""
        INSERT OR IGNORE INTO users (username, password, role, display_name)
        VALUES (?, ?, ?, ?)
    """, [
        ("admin@messmind.edu", "admin123", "admin", "Admin Incharge"),
        ("LPU002", "student123", "student", "Ganesh Reddy"),
        ("LPU003", "student123", "student", "Rohith"),
        ("LPU004", "student123", "student", "HarinathReddy"),
        ("LPU005", "student123", "student", "Tharun")
    ])

    # Seed default students
    cursor.executemany("""
        INSERT OR IGNORE INTO students (name, student_id)
        VALUES (?, ?)
    """, [
        ("Ganesh Reddy", "LPU002"),
        ("Rohith", "LPU003"),
        ("HarinathReddy", "LPU004"),
        ("Tharun", "LPU005")
    ])

    # Seed sample records if empty
    cursor.execute("SELECT COUNT(*) FROM waste_records")
    if cursor.fetchone()[0] == 0:
        today_str = datetime.now().strftime("%Y-%m-%d")
        sample_records = [
            ("Ganesh Reddy", "LPU002", "Lunch", 120, today_str, "12:45 PM", "Recorded"),
            ("Rohith", "LPU003", "Lunch", 75, today_str, "12:38 PM", "Recorded"),
            ("HarinathReddy", "LPU004", "Breakfast", 260, today_str, "08:20 AM", "High"),
            ("Tharun", "LPU005", "Breakfast", 90, today_str, "08:05 AM", "Recorded")
        ]
        cursor.executemany("""
            INSERT INTO waste_records (student_name, student_id, meal, weight, record_date, record_time, flag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_records)

    conn.commit()
    conn.close()


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/login.html")
def login_page():
    return send_from_directory(BASE_DIR, "login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "user": {
                "username": user["username"],
                "role": user["role"],
                "displayName": user["display_name"],
                "studentId": user["username"] if user["role"] == "student" else ""
            }
        })
    else:
        # Flexible login fallback for development demo
        role = "admin" if "@" in username or "admin" in username.lower() else "student"
        return jsonify({
            "status": "success",
            "user": {
                "username": username,
                "role": role,
                "displayName": username.split("@")[0].upper() if "@" in username else username,
                "studentId": username if role == "student" else ""
            }
        })


@app.route("/api/records", methods=["GET"])
def get_records():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM waste_records ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    records = [
        {
            "id": r["id"],
            "name": r["student_name"],
            "studentId": r["student_id"],
            "meal": r["meal"],
            "weight": r["weight"],
            "date": r["record_date"],
            "time": r["record_time"],
            "flag": r["flag"]
        }
        for r in rows
    ]
    return jsonify(records)


@app.route("/api/records", methods=["POST"])
def add_record():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    student_id = data.get("studentId", "").strip()
    meal = data.get("meal", "Lunch")
    weight = float(data.get("weight", 0))

    if not name or weight <= 0:
        return jsonify({"error": "Invalid data"}), 400

    now = datetime.now()
    record_date = now.strftime("%Y-%m-%d")
    record_time = now.strftime("%I:%M %p")
    flag = "High" if weight >= 250 else "Recorded"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO waste_records (student_name, student_id, meal, weight, record_date, record_time, flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, student_id, meal, weight, record_date, record_time, flag))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "status": "success",
        "record": {
            "id": new_id,
            "name": name,
            "studentId": student_id,
            "meal": meal,
            "weight": weight,
            "date": record_date,
            "time": record_time,
            "flag": flag
        }
    }), 201


@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT weight, student_id FROM waste_records WHERE record_date = ?", (today_str,))
    today_rows = cursor.fetchall()

    today_total = sum(r["weight"] for r in today_rows)
    student_count = len(set(r["student_id"] for r in today_rows))
    avg_waste = round(today_total / max(1, len(today_rows))) if today_rows else 0

    cursor.execute("SELECT weight FROM waste_records")
    all_weights = [r["weight"] for r in cursor.fetchall()]
    all_total = sum(all_weights)
    max_event = max(all_weights) if all_weights else 0

    conn.close()

    return jsonify({
        "todayTotalGrams": today_total,
        "todayTotalKg": round(today_total / 1000.0, 2),
        "studentCount": student_count,
        "averageWasteGrams": avg_waste,
        "allTotalKg": round(all_total / 1000.0, 2),
        "highestEventGrams": max_event
    })


if __name__ == "__main__":
    init_db()
    print("==================================================")
    print("MessMind Flask Server is running!")
    print("Database: messmind.db (SQLite)")
    print("Local access:   http://127.0.0.1:5000")
    print("Network access: http://10.36.7.105:5000")
    print("==================================================")
    app.run(host="0.0.0.0", port=5000, debug=False)
