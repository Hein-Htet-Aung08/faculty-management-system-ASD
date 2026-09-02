import sqlite3
import os
from pathlib import Path

DATA_DIR = os.getenv("DB_PATH", str(Path(__file__).parent / "staff.db"))
conn = sqlite3.connect(DATA_DIR)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()


# ---------- DEPARTMENTS ----------- 
departments = [
    (1, "Computer Science", "Faculty of Science and Engineering"),
    (2, "Information Technology", "Faculty of Science and Engineering"),
    (3, "Mechanical Engineering", "Faculty of Science and Engineering"),
    (4, "Accounting", "Faculty of Business"),
    (5, "Marketing", "Faculty of Business"),
    (6, "Management", "Faculty of Business"),
    (7, "Nursing", "Faculty of Health"),
    (8, "Public Health", "Faculty of Health"),
    (9, "Psychology", "Faculty of Arts"),
    (10, "Sociology", "Faculty of Arts")
    ]

cursor.executemany(
    """
    INSERT INTO departments (
        department_id,
        department_name,
        faculty
    )
    VALUES (?, ?, ?)
    """,
    departments
)

# ---------- STAFF ----------- 
staff = [
    (1, "John Smith", "john.smith@university.edu", "0412345678", 1, "Senior Lecturer", "Full-time", "Active"),
    (2, "Grace Tan", "grace.tan@university.edu", "0412345679", 1, "Lecturer", "Full-time", "Active"),
    (3, "Marcus Chen", "marcus.chen@university.edu", "0412345680", 2, "Senior Lecturer", "Full-time", "Active"),
    (4, "Priya Nair", "priya.nair@university.edu", "0412345681", 2, "Associate Lecturer", "Part-time", "Active"),
    (5, "David Kim", "david.kim@university.edu", "0412345682", 3, "Professor", "Full-time", "On Leave"),
    (6, "Fatima Ali", "fatima.ali@university.edu", "0412345683", 4, "Lecturer", "Full-time", "Active"),
    (7, "Ben Robertson", "ben.robertson@university.edu", "0412345684", 5, "Senior Lecturer", "Full-time", "Active"),
    (8, "Hana Suzuki", "hana.suzuki@university.edu", "0412345685", 6, "Lecturer", "Part-time", "Active"),
    (9, "Carlos Mendes", "carlos.mendes@university.edu", "0412345686", 7, "Clinical Lecturer", "Full-time", "Active"),
    (10, "Olivia Bennett", "olivia.bennett@university.edu", "0412345687", 9, "Senior Lecturer", "Full-time", "Inactive")
]

cursor.executemany(
    """
    INSERT INTO staff (
        staff_id,
        name,
        email,
        phone, 
        department_id, 
        position,
        employment_type, 
        status 
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
    staff
)

# ---------- STAFF QUALIFICATIONS ----------- 
staff_qualifications = [
    (1, 1, "PhD in Computer Science", "University of Sydney", 2015),
    (2, 2, "Master of Information Technology", "University of Melbourne", 2018),
    (3, 3, "PhD in Software Engineering", "UNSW", 2012),
    (4, 4, "Master of Computer Science", "Monash University", 2019),
    (5, 5, "PhD in Mechanical Engineering", "University of Queensland", 2008),
    (6, 6, "Master of Accounting", "University of Sydney", 2016),
    (7, 7, "MBA (Marketing)", "RMIT University", 2014),
    (8, 8, "Master of Business Administration", "University of Melbourne", 2017),
    (9, 9, "Master of Nursing", "Deakin University", 2013),
    (10, 10, "PhD in Psychology", "University of Sydney", 2010)
]

cursor.executemany(
    """
    INSERT INTO staff_qualifications (
        qualification_id, 
        staff_id, 
        qualification_name, 
        institution, 
        year_obtained 
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    staff_qualifications
)

# ---------- STAFF EXPERTISE ----------- 
staff_expertise = [
    (1, 1, "Machine Learning", 5),
    (2, 2, "Cloud Computing", 4),
    (3, 3, "Software Architecture", 5),
    (4, 4, "Database Systems", 3),
    (5, 5, "Robotics", 5),
    (6, 6, "Financial Reporting", 4),
    (7, 7, "Digital Marketing", 4),
    (8, 8, "Strategic Management", 3),
    (9, 9, "Clinical Practice", 5),
    (10, 10, "Cognitive Psychology", 5)
]

cursor.executemany(
    """
    INSERT INTO staff_expertise (
        expertise_id, 
        staff_id,
        expertise_area, 
        skill_level
    )
    VALUES (?, ?, ?, ?)
    """,
    staff_expertise
)

# ---------- STAFF AVAILABILITY ----------- 
staff_availability = [
    (1, 1, "Monday", "09:00-11:00", "Available"),
    (2, 2, "Tuesday", "10:00-12:00", "Available"),
    (3, 3, "Wednesday", "13:00-15:00", "Available"),
    (4, 4, "Monday", "14:00-16:00", "Unavailable"),
    (5, 5, "Thursday", "09:00-11:00", "On Leave"),
    (6, 6, "Friday", "11:00-13:00", "Available"),
    (7, 7, "Tuesday", "15:00-17:00", "Available"),
    (8, 8, "Wednesday", "09:00-11:00", "Available"),
    (9, 9, "Thursday", "13:00-15:00", "Available"),
    (10, 10, "Friday", "10:00-12:00", "Unavailable"),
]

cursor.executemany(
    """
    INSERT INTO staff_availability (
        availability_id, 
        staff_id, 
        day, 
        time_slot, 
        availability_status 
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    staff_availability
)

# ---------- STAFF AI ANALYSIS ----------- 
staff_ai_analysis = [
    (1, 1, "John Smith demonstrates strong expertise in Machine Learning, supported by a PhD in Computer Science and a senior academic role, making them highly suitable for advanced AI-related subjects.", 9.2, "2026-08-20"),
    (2, 2, "Grace Tan shows solid proficiency in Cloud Computing, backed by a relevant Master's qualification, suitable for intermediate to advanced infrastructure-focused subjects.", 7.8, "2026-08-20"),
    (3, 3, "Marcus Chen exhibits excellent capability in Software Architecture, reinforced by a PhD in Software Engineering, well suited to advanced systems design subjects.", 9.0, "2026-08-20"),
    (4, 4, "Priya Nair holds moderate proficiency in Database Systems, appropriate for introductory to intermediate database subjects given their part-time status.", 6.1, "2026-08-20"),
    (5, 5, "David Kim possesses expert-level knowledge in Robotics, though currently on leave, which should be factored into scheduling recommendations.", 8.9, "2026-08-20"),
    (6, 6, "Fatima Ali demonstrates strong competency in Financial Reporting, well aligned with accounting-focused subject delivery.", 7.9, "2026-08-20"),
    (7, 7, "Ben Robertson shows strong expertise in Digital Marketing, suitable for marketing strategy and campaign-focused subjects.", 7.7, "2026-08-20"),
    (8, 8, "Hana Suzuki has moderate proficiency in Strategic Management, appropriate for foundational management subjects given part-time availability.", 6.4, "2026-08-20"),
    (9, 9, "Carlos Mendes demonstrates excellent clinical expertise, highly suitable for hands-on clinical practice subjects.", 9.1, "2026-08-20"),
    (10, 10, "Olivia Bennett exhibits expert-level knowledge in Cognitive Psychology, though currently inactive, which should be factored into availability planning.", 8.8, "2026-08-20")
]

cursor.executemany(
    """
    INSERT INTO staff_ai_analysis (
        analysis_id, 
        staff_id, 
        generated_summary,
        suitability_score, 
        date_generated 
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    staff_ai_analysis
)

# ---------- STAFF AI RECOMMENDED SUBJECTS ----------- 
staff_ai_recommended_subjects = [
    (1, 1, "Introduction to Machine Learning"),
    (2, 2, "Cloud Infrastructure and Deployment"),
    (3, 3, "Advanced Software Architecture"),
    (4, 4, "Database Systems Fundamentals"),
    (5, 5, "Robotics and Automation"),
    (6, 6, "Financial Accounting Principles"),
    (7, 7, "Digital Marketing Strategy"),
    (8, 8, "Foundations of Strategic Management"),
    (9, 9, "Clinical Nursing Practice"),
    (10, 10, "Cognitive Psychology Foundations")
]

cursor.executemany(
    """
    INSERT INTO staff_ai_recommended_subjects (
        recommendation_id, 
        analysis_id, 
        subject_name 
    )
    VALUES (?, ?, ?)
    """,
    staff_ai_recommended_subjects
)

conn.commit()
conn.close()
print("Database seeded successfully")