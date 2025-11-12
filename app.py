from flask import Flask, jsonify, request
import mysql.connector

app = Flask(__name__)

def get_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="academic_portal"
    )

@app.route('/')
def home():
    return "Academic Portal API is running!"

# 1️⃣ Fetch all students
@app.route('/students', methods=['GET'])
def get_students():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.student_id, s.name, s.email, d.name AS department, f.name AS mentor
        FROM students s
        JOIN departments d ON s.dept_id = d.dept_id
        LEFT JOIN faculty f ON s.mentor_id = f.faculty_id
    """)
    students = cur.fetchall()
    conn.close()
    return jsonify(students)

# 2️⃣ Fetch all faculty
@app.route('/faculty', methods=['GET'])
def get_faculty():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT f.faculty_id, f.name, f.email, d.name AS department, f.designation
        FROM faculty f
        JOIN departments d ON f.dept_id = d.dept_id
    """)
    faculty = cur.fetchall()
    conn.close()
    return jsonify(faculty)

# 3️⃣ Add a new student (example)
@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.get_json()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students (user_id, roll_no, name, email, dept_id, year, batch, mentor_id, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """, (data['user_id'], data['roll_no'], data['name'], data['email'], data['dept_id'], data['year'], data['batch'], data['mentor_id']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Student added successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True)
