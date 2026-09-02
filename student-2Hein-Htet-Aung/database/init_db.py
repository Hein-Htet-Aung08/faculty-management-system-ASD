import os
import sqlite3

DATA_DIR = "/app/data"
DATABASE_NAME = os.path.join(DATA_DIR, "allocation.db")

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(
    DATABASE_NAME
)

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    subject_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    required_expertise TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subject_offers (
    offer_id TEXT PRIMARY KEY,
    subject_code TEXT NOT NULL,
    semester TEXT NOT NULL,
    year TEXT NOT NULL,
    expected_enrollment INTEGER NOT NULL,
    FOREIGN KEY (subject_code)
        REFERENCES subjects(subject_code)
        ON DELETE RESTRICT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS classrooms (
    classroom_id TEXT PRIMARY KEY,
    building TEXT NOT NULL,
    floor TEXT NOT NULL,
    room_number TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    facilities TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS teaching_allocations (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id TEXT NOT NULL,
    assigned_staff_member INTEGER NOT NULL,
    classroom_id TEXT NOT NULL,
    day TEXT NOT NULL,
    date_range TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    class_type TEXT NOT NULL,
    expected_class_size INTEGER NOT NULL,
    allocation_status TEXT NOT NULL,
    FOREIGN KEY (offer_id)
        REFERENCES subject_offers(offer_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (classroom_id)
        REFERENCES classrooms(classroom_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
)
""")

cursor.execute(
    "DELETE FROM teaching_allocations"
)

cursor.execute(
    "DELETE FROM subject_offers"
)

cursor.execute(
    "DELETE FROM classrooms"
)

cursor.execute(
    "DELETE FROM subjects"
)

subjects = [
    ("41082", "Introduction to Data Engineering", "Data Engineering,Databases"),
    ("41080", "Theory of Computing", "Algorithms,Computation Theory"),
    ("41113", "Software Architecture", "Software Engineering,Architecture"),
    ("41114", "Advanced Software Development", "Software Engineering,DevOps,Agentic AI"),
    ("31271", "Database Fundamentals", "Databases,SQL"),
    ("31268", "Web Systems", "Web Development,HTTP"),
    ("41092", "Network Fundamentals", "Networking,Infrastructure"),
    ("41095", "Cybersecurity", "Security,Networking"),
    ("41180", "Interactive Media", "UI Design,Frontend Development"),
    ("41039", "Programming Fundamentals", "Programming,Software Development"),
]

cursor.executemany(
    """
    INSERT INTO subjects (
        subject_code,
        name,
        required_expertise
    )
    VALUES (?, ?, ?)
    """,
    subjects
)

subject_offers = [
    ("41082_SPR_2026", "41082", "SPR", "2026", 180),
    ("41080_SPR_2026", "41080", "SPR", "2026", 160),
    ("41113_SPR_2026", "41113", "SPR", "2026", 150),
    ("41114_SPR_2026", "41114", "SPR", "2026", 120),
    ("31271_SPR_2026", "31271", "SPR", "2026", 200),
    ("31268_SPR_2026", "31268", "SPR", "2026", 190),
    ("41092_SPR_2026", "41092", "SPR", "2026", 130),
    ("41095_SPR_2026", "41095", "SPR", "2026", 110),
    ("41180_SPR_2026", "41180", "SPR", "2026", 100),
    ("41039_SPR_2026", "41039", "SPR", "2026", 220),
]

cursor.executemany(
    """
    INSERT INTO subject_offers (
        offer_id,
        subject_code,
        semester,
        year,
        expected_enrollment
    )
    VALUES (?, ?, ?, ?, ?)
    """,
    subject_offers
)

classrooms = [
    ("CB11.04.405", "CB11", "04", "405", 120, "Tutorial Room", "Projector,Whiteboard"),
    ("CB11.04.406", "CB11", "04", "406", 120, "Tutorial Room", "Projector,Whiteboard"),
    ("CB11.05.501", "CB11", "05", "501", 200, "Lecture Theatre", "Projector,Microphone"),
    ("CB11.05.502", "CB11", "05", "502", 180, "Lecture Theatre", "Projector,Microphone"),
    ("CB10.02.301", "CB10", "02", "301", 30, "Computer Lab", "Computers,Projector"),
    ("CB10.02.302", "CB10", "02", "302", 30, "Computer Lab", "Computers,Projector"),
    ("CB10.03.401", "CB10", "03", "401", 40, "Tutorial Room", "Projector,Whiteboard"),
    ("CB10.03.402", "CB10", "03", "402", 40, "Tutorial Room", "Projector,Whiteboard"),
    ("CB02.01.101", "CB02", "01", "101", 250, "Lecture Theatre", "Projector,Microphone"),
    ("CB02.01.102", "CB02", "01", "102", 100, "Seminar Room", "Projector,Whiteboard"),
]

cursor.executemany(
    """
    INSERT INTO classrooms (
        classroom_id,
        building,
        floor,
        room_number,
        capacity,
        room_type,
        facilities
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    classrooms
)

teaching_allocations = [
    ("41082_SPR_2026", 1, "CB11.05.501", "MON", "03/08 - 20/09", "10:00", "12:00", "LEC", 180, "CONFIRMED"),
    ("41080_SPR_2026", 2, "CB11.05.502", "TUE", "03/08 - 20/09", "09:00", "11:00", "LEC", 160, "CONFIRMED"),
    ("41113_SPR_2026", 3, "CB11.04.405", "WED", "03/08 - 20/09", "12:00", "14:00", "TUT", 30, "CONFIRMED"),
    ("41114_SPR_2026", 4, "CB11.04.406", "THU", "03/08 - 20/09", "14:00", "16:00", "TUT", 30, "PENDING"),
    ("31271_SPR_2026", 5, "CB10.02.301", "FRI", "03/08 - 20/09", "10:00", "12:00", "LAB", 30, "CONFIRMED"),
    ("31268_SPR_2026", 6, "CB10.02.302", "MON", "03/08 - 20/09", "14:00", "16:00", "LAB", 30, "CONFIRMED"),
    ("41092_SPR_2026", 7, "CB10.03.401", "TUE", "03/08 - 20/09", "12:00", "14:00", "TUT", 40, "CONFIRMED"),
    ("41095_SPR_2026", 8, "CB10.03.402", "WED", "03/08 - 20/09", "10:00", "12:00", "TUT", 40, "PENDING"),
    ("41180_SPR_2026", 9, "CB02.01.102", "THU", "03/08 - 20/09", "10:00", "12:00", "SEM", 100, "CONFIRMED"),
    ("41039_SPR_2026", 10, "CB02.01.101", "FRI", "03/08 - 20/09", "09:00", "11:00", "LEC", 220, "CONFIRMED"),
]

cursor.executemany(
    """
    INSERT INTO teaching_allocations (
        offer_id,
        assigned_staff_member,
        classroom_id,
        day,
        date_range,
        start_time,
        end_time,
        class_type,
        expected_class_size,
        allocation_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    teaching_allocations
)

conn.commit()
conn.close()

print(
    "Database initialized."
)