import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent/"staff.db"
conn = sqlite3.connect(DATA_DIR)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL,
    faculty TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff (
    staff_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    department_id INTEGER NOT NULL,
    position TEXT NOT NULL, 
    employment_type TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_qualifications (
    qualification_id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    qualification_name TEXT NOT NULL,
    institution TEXT,
    year_obtained INTEGER,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_expertise (
    expertise_id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    expertise_area TEXT NOT NULL,   
    skill_level INTEGER NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_availability (
    availability_id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_ai_analysis (
    analysis_id INTEGER PRIMARY KEY,
    staff_id INTEGER NOT NULL,
    generated_summary TEXT NOT NULL,
    suitability_score REAL NOT NULL,
    date_generated TEXT NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS staff_ai_recommended_subjects (
    recommendation_id INTEGER PRIMARY KEY,
    analysis_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES staff_ai_analysis(analysis_id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()
print("Databases Initialisation Successful")