import mysql.connector
from datetime import datetime, date, timedelta
from faker import Faker
import random, uuid

fake = Faker()

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "academic_portal",
    "autocommit": False
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def rand_semester():
    return f"Sem-{random.randint(1,8)}-2025"

def seed_data():
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Departments
        dept_ids = []
        for d in ["Computer Science", "Electronics", "Mechanical", "Mathematics", "Physics", "Chemistry"]:
            cur.execute("""
                INSERT IGNORE INTO departments (name, created_at)
                VALUES (%s,%s)
            """, (d, datetime.now()))
            cur.execute("SELECT dept_id FROM departments WHERE name=%s", (d,))
            dept_ids.append(cur.fetchone()[0])

        # Users + Faculty
        faculty_ids = []
        for i in range(10):
            uname = f"fac{i}"
            urole = "faculty"
            cur.execute("""
                INSERT IGNORE INTO users (username, password_hash, role, created_at)
                VALUES (%s,%s,%s,%s)
            """, (uname, f"hash{i}", urole, datetime.now()))
            cur.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
            uid = cur.fetchone()[0]
            dept = random.choice(dept_ids)
            cur.execute("""
                INSERT IGNORE INTO faculty (user_id, name, email, dept_id, designation, created_at)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (uid, fake.name(), fake.email(), dept, random.choice(["Professor","Assistant Professor","Lecturer"]), datetime.now()))
            cur.execute("SELECT faculty_id FROM faculty WHERE user_id=%s", (uid,))
            faculty_ids.append(cur.fetchone()[0])

        # Users + Students
        student_ids = []
        for i in range(20):
            uname = f"stud{i}"
            cur.execute("""
                INSERT IGNORE INTO users (username, password_hash, role, created_at)
                VALUES (%s,%s,%s,%s)
            """, (uname, f"hash_s{i}", "student", datetime.now()))
            cur.execute("SELECT user_id FROM users WHERE username=%s", (uname,))
            uid = cur.fetchone()[0]
            dept = random.choice(dept_ids)
            mentor = random.choice(faculty_ids)
            cur.execute("""
                INSERT IGNORE INTO students (user_id, roll_no, name, email, dept_id, year, batch, mentor_id, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (uid, f"{dept}_{i:03d}", fake.name(), fake.email(), dept, random.randint(1,4), 2025, mentor, datetime.now()))
            cur.execute("SELECT student_id FROM students WHERE user_id=%s", (uid,))
            student_ids.append(cur.fetchone()[0])

        # Sessions (for random users)
        for uid in random.sample(student_ids + faculty_ids, 10):
            session_id = str(uuid.uuid4())
            cur.execute("""
                INSERT IGNORE INTO sessions (session_id, user_id, token_hash, created_at, expires_at)
                VALUES (%s,%s,%s,%s,%s)
            """, (session_id, uid, f"tok_{uid}", datetime.now(), None))

        # Courses
        course_codes = ["CS101","CS102","EC101","MA101","ME101","PH101","CH101","CS201","EC201","MA201"]
        for code in course_codes:
            cur.execute("""
                INSERT IGNORE INTO courses (course_id, title, credits, dept_id, description, created_at)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (code, fake.catch_phrase(), random.choice([3.0,4.0]), random.choice(dept_ids), fake.sentence(), datetime.now()))

        # Course Offerings
        offering_ids = []
        for code in course_codes:
            for _ in range(2):
                cur.execute("""
                    INSERT INTO course_offerings (course_id, semester, academic_year, faculty_id, internal_weight, external_weight, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (code, rand_semester(), "2025", random.choice(faculty_ids), 40, 60, datetime.now()))
                offering_ids.append(cur.lastrowid)

        # Enrollments
        enrollment_ids = []
        for sid in student_ids:
            for off in random.sample(offering_ids, 3):
                cur.execute("""
                    INSERT IGNORE INTO enrollments (offering_id, student_id, status, enrollment_date)
                    VALUES (%s,%s,%s,%s)
                """, (off, sid, random.choice(["enrolled","completed"]), datetime.now()))
                cur.execute("SELECT enroll_id FROM enrollments WHERE offering_id=%s AND student_id=%s", (off, sid))
                enrollment_ids.append(cur.fetchone()[0])

        # Assessment Components
        comp_ids = []
        for off in offering_ids:
            for cname, w, ctype in [("IA1",15,"internal"),("IA2",15,"internal"),("Final",70,"external")]:
                cur.execute("""
                    INSERT IGNORE INTO assessment_components (offering_id, component_name, component_type, max_marks, weight_percent, sequence_no, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (off, cname, ctype, 100, w, random.randint(1,3), datetime.now()))
                cur.execute("SELECT component_id FROM assessment_components WHERE offering_id=%s AND component_name=%s", (off, cname))
                comp_ids.append(cur.fetchone()[0])

        # Assessment Scores
        for enr in random.sample(enrollment_ids, 50):
            for comp in random.sample(comp_ids, 3):
                cur.execute("""
                    INSERT IGNORE INTO assessment_scores (enroll_id, component_id, marks_obtained, recorded_by, recorded_at)
                    VALUES (%s,%s,%s,%s,%s)
                """, (enr, comp, random.randint(20,100), random.choice(faculty_ids), datetime.now()))

        # Attendance Records
        for enr in random.sample(enrollment_ids, 40):
            for _ in range(5):
                cur.execute("""
                    INSERT IGNORE INTO attendance_records (enroll_id, session_date, session_type, present, recorder_id, remarks, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (enr, date.today()-timedelta(days=random.randint(1,30)), "lecture", random.choice([True,False]), random.choice(faculty_ids), fake.word(), datetime.now()))

        # Attendance Summary
        for enr in enrollment_ids:
            cur.execute("""
                INSERT INTO attendance_summary (enroll_id, total_sessions, present_count, last_updated)
                VALUES (%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE total_sessions=VALUES(total_sessions), present_count=VALUES(present_count)
            """, (enr, 10, random.randint(5,10), datetime.now()))

        # Grade Scale
        grades = [(90,100,'A+',10),(80,89.99,'A',9),(70,79.99,'B',8),(60,69.99,'C',7),(50,59.99,'D',6),(0,49.99,'F',0)]
        for g in grades:
            cur.execute("""
                INSERT IGNORE INTO grade_scale (min_perc, max_perc, grade, grade_point)
                VALUES (%s,%s,%s,%s)
            """, g)

        # Final Results
        for enr in enrollment_ids:
            marks = random.randint(40,100)
            gp = 10 if marks>=90 else 9 if marks>=80 else 8 if marks>=70 else 7 if marks>=60 else 6 if marks>=50 else 0
            grade = 'A+' if marks>=90 else 'A' if marks>=80 else 'B' if marks>=70 else 'C' if marks>=60 else 'D' if marks>=50 else 'F'
            cur.execute("""
                INSERT INTO final_results (enroll_id, final_marks, grade, grade_point, passed, computed_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE final_marks=VALUES(final_marks), grade=VALUES(grade), grade_point=VALUES(grade_point), passed=VALUES(passed)
            """, (enr, marks, grade, gp, marks>=40, datetime.now()))

        # GPA Records
        for sid in student_ids:
            gpa = round(random.uniform(6.0,10.0),2)
            cur.execute("""
                INSERT INTO gpa_records (student_id, semester, total_credits, weighted_grade_points, gpa, created_at)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE total_credits=VALUES(total_credits), weighted_grade_points=VALUES(weighted_grade_points), gpa=VALUES(gpa)
            """, (sid, rand_semester(), random.uniform(15,25), random.uniform(80,150), gpa, datetime.now()))

        conn.commit()
        print("✅ Successfully seeded interconnected data (duplicates skipped).")

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        print("❌ Error:", err)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    seed_data()
