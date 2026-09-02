import os
import sqlite3

from schema import TABLES, create_table_sql

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATABASE_NAME = os.path.join(DATA_DIR, "workload.db")

os.makedirs(DATA_DIR, exist_ok=True)

SEMESTER = "2026-S2"

# --------------------------------------------------------------------- seeds ---

STAFF_WORKLOAD_PROFILE = [
    # profile_id, staff_id, staff_name, department, semester, contracted_fraction,
    # max_weekly_hours, current_total_hours, status
    (1, 1, "Dr Alice Nguyen", "Computing", SEMESTER, 1.0, 37.5, 41.0, "overloaded"),
    (2, 2, "Dr Ben Carter", "Computing", SEMESTER, 1.0, 37.5, 36.0, "ok"),
    (3, 3, "Prof Chloe Davis", "Computing", SEMESTER, 0.8, 30.0, 21.0, "underloaded"),
    (4, 4, "Dr Daniel Okoro", "Engineering", SEMESTER, 1.0, 37.5, 39.5, "overloaded"),
    (5, 5, "Dr Elena Rossi", "Engineering", SEMESTER, 1.0, 37.5, 33.0, "ok"),
    (6, 6, "Dr Farid Hassan", "Engineering", SEMESTER, 0.6, 22.5, 12.0, "underloaded"),
    (7, 7, "Dr Grace Lin", "Design", SEMESTER, 1.0, 37.5, 37.0, "ok"),
    (8, 8, "Dr Henry Adams", "Design", SEMESTER, 0.5, 18.75, 20.0, "overloaded"),
    (9, 9, "Dr Isla Murphy", "Business", SEMESTER, 1.0, 37.5, 28.0, "underloaded"),
    (10, 10, "Dr Jack Wilson", "Business", SEMESTER, 1.0, 37.5, 37.5, "ok"),
    (11, 11, "Dr Kavya Rao", "Science", SEMESTER, 0.8, 30.0, 34.0, "overloaded"),
    (12, 12, "Dr Liam Brown", "Science", SEMESTER, 1.0, 37.5, 30.0, "ok"),
]

WORKLOAD_ENTRY = [
    # entry_id, staff_id, activity_type, description, hours_per_week,
    # start_date, end_date, semester, source_service
    (1, 1, "teaching", "31266 Introduction to Software Development", 14.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (2, 1, "teaching", "48024 Programming Fundamentals tutorials", 9.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (3, 1, "research", "ARC Discovery grant - agentic systems", 12.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (4, 1, "service", "Course coordination - Bachelor of IT", 6.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (5, 2, "teaching", "41092 Network Fundamentals", 16.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (6, 2, "professional_development", "Learning & teaching micro-credential", 4.0, "2026-08-01", "2026-10-30", SEMESTER, "performance-dev"),
    (7, 2, "admin", "Timetabling working group", 16.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (8, 3, "teaching", "32555 Fundamentals of Interaction Design", 11.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (9, 3, "research", "Supervision - 3 HDR candidates", 10.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (10, 4, "teaching", "48610 Introduction to Electrical Engineering", 18.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (11, 4, "research", "Industry project - renewable microgrids", 15.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (12, 4, "service", "Faculty board member", 6.5, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (13, 5, "teaching", "48620 Engineering Mechanics", 20.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (14, 5, "professional_development", "WHS refresher training", 3.0, "2026-08-10", "2026-08-24", SEMESTER, "performance-dev"),
    (15, 5, "admin", "Lab safety officer", 10.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (16, 6, "teaching", "48023 Programming for Engineers", 12.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (17, 7, "teaching", "88611 Integrating Design Futures", 22.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (18, 7, "service", "Studio coordination", 15.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (19, 8, "teaching", "83525 Design Research Methods", 14.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (20, 8, "research", "Exhibition catalogue authoring", 6.0, "2026-08-01", "2026-11-30", SEMESTER, "research-grant"),
    (21, 9, "teaching", "21129 Managing People and Organisations", 16.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (22, 9, "professional_development", "Case-method teaching workshop", 4.0, "2026-09-01", "2026-09-30", SEMESTER, "performance-dev"),
    (23, 10, "teaching", "22107 Accounting for Business Decisions", 21.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (24, 10, "service", "Admissions interviewer", 16.5, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (25, 11, "teaching", "65111 Chemistry 1", 19.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (26, 11, "research", "NHMRC ideas grant - catalysis", 15.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (27, 12, "teaching", "68036 Physics for Scientists", 20.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (28, 12, "admin", "First-year experience coordinator", 10.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
]

AVAILABILITY_SLOT = [
    # slot_id, staff_id, day_of_week, start_time, end_time, availability, is_recurring
    (1, 1, "Mon", "09:00", "12:00", "available", 1),
    (2, 1, "Mon", "13:00", "17:00", "available", 1),
    (3, 1, "Wed", "09:00", "13:00", "preferred", 1),
    (4, 1, "Fri", "00:00", "23:59", "unavailable", 1),
    (5, 2, "Tue", "09:00", "17:00", "available", 1),
    (6, 2, "Thu", "09:00", "17:00", "available", 1),
    (7, 3, "Mon", "10:00", "15:00", "available", 1),
    (8, 3, "Wed", "10:00", "15:00", "preferred", 1),
    (9, 4, "Mon", "08:00", "16:00", "available", 1),
    (10, 4, "Tue", "08:00", "16:00", "available", 1),
    (11, 5, "Wed", "09:00", "17:00", "available", 1),
    (12, 6, "Thu", "09:00", "13:00", "available", 1),
    (13, 7, "Mon", "09:00", "18:00", "preferred", 1),
    (14, 8, "Fri", "09:00", "13:00", "available", 1),
    (15, 9, "Tue", "09:00", "17:00", "available", 1),
    (16, 10, "Mon", "09:00", "17:00", "available", 1),
    (17, 11, "Wed", "08:00", "12:00", "available", 1),
    (18, 12, "Thu", "12:00", "18:00", "preferred", 1),
]

LEAVE_RECORD = [
    # leave_id, staff_id, leave_type, start_date, end_date, reason, approval
    (1, 1, "conference", "2026-09-14", "2026-09-18", "ICSE presentation", "approved"),
    (2, 3, "long_service", "2026-10-05", "2026-10-30", "Long service leave block", "approved"),
    (3, 4, "sick", "2026-08-24", "2026-08-26", "Medical certificate provided", "approved"),
    (4, 5, "annual", "2026-09-28", "2026-10-02", "Family holiday", "pending"),
    (5, 6, "parental", "2026-08-01", "2026-12-15", "Parental leave - 0.4 backfill", "approved"),
    (6, 7, "conference", "2026-11-02", "2026-11-06", "Design research symposium", "pending"),
    (7, 8, "annual", "2026-09-21", "2026-09-25", "Annual leave", "approved"),
    (8, 9, "sick", "2026-08-18", "2026-08-19", "Short illness", "approved"),
    (9, 10, "annual", "2026-10-12", "2026-10-16", "Annual leave", "rejected"),
    (10, 11, "conference", "2026-09-07", "2026-09-11", "RACI national congress", "approved"),
    (11, 12, "annual", "2026-11-09", "2026-11-13", "Annual leave", "pending"),
]

WORKLOAD_RULE = [
    # rule_id, name, applies_to, max_total_hours, warning_threshold
    (1, "University standard full-time cap", "all", 37.5, 35.0),
    (2, "Computing faculty cap", "Computing", 38.0, 34.0),
    (3, "Engineering faculty cap", "Engineering", 38.0, 34.0),
    (4, "Design faculty cap", "Design", 37.5, 33.0),
    (5, "Business faculty cap", "Business", 37.5, 34.0),
    (6, "Science faculty cap", "Science", 38.0, 34.0),
    (7, "Teaching activity soft cap", "all", 24.0, 20.0),
    (8, "Research minimum for research-active", "all", 40.0, 8.0),
    (9, "Fractional (0.5) appointment cap", "all", 18.75, 16.0),
    (10, "Fractional (0.8) appointment cap", "all", 30.0, 27.0),
    (11, "Admin/service soft cap", "all", 16.0, 12.0),
]

WORKLOAD_ALERT = [
    # alert_id, staff_id, alert_type, severity, message, status, date_raised
    (1, 1, "overload", "high", "Total 41.0h exceeds Computing cap 38.0h", "open", "2026-08-20"),
    (2, 1, "clash", "medium", "Wed research block overlaps CB11 tutorial 10:00-12:00", "open", "2026-08-20"),
    (3, 4, "overload", "high", "Total 39.5h exceeds Engineering cap 38.0h", "open", "2026-08-20"),
    (4, 8, "overload", "medium", "Total 20.0h exceeds 0.5 fractional cap 18.75h", "acknowledged", "2026-08-19"),
    (5, 11, "overload", "high", "Total 34.0h exceeds 0.8 fractional cap 30.0h", "open", "2026-08-21"),
    (6, 3, "underload", "low", "Total 21.0h below 0.8 warning threshold 27.0h", "open", "2026-08-21"),
    (7, 6, "underload", "medium", "Total 12.0h below 0.6 expected load", "open", "2026-08-21"),
    (8, 9, "underload", "low", "Total 28.0h below full-time warning threshold 35.0h", "open", "2026-08-21"),
    (9, 5, "clash", "medium", "Requested annual leave overlaps 48620 teaching weeks", "open", "2026-08-22"),
    (10, 7, "clash", "low", "Conference leave overlaps final teaching week", "open", "2026-08-22"),
    (11, 10, "overload", "low", "Total 37.5h at full-time cap - no headroom", "acknowledged", "2026-08-22"),
]

REBALANCE_RECOMMENDATION = [
    # rec_id, alert_id, staff_id, suggested_action, target_staff_id, rationale, decision_status
    (1, 1, 1, "Move 48024 tutorials (9.0h) to Dr Ben Carter", 2, "Carter has 1.5h headroom and teaches adjacent networking subject", "pending"),
    (2, 1, 1, "Reduce course coordination from 6.0h to 3.0h", None, "Coordination is above the admin soft cap for a research-active staff member", "pending"),
    (3, 3, 4, "Transfer industry project oversight (15.0h) partly to Dr Elena Rossi", 5, "Rossi is at 33.0h with 4.5h headroom before threshold", "pending"),
    (4, 4, 8, "Shift exhibition catalogue authoring (6.0h) to next semester", None, "Task is not time-critical and staff is on a 0.5 fraction", "accepted"),
    (5, 5, 11, "Move 65111 lab supervision (approx 5.0h) to Dr Liam Brown", 12, "Brown has 7.5h headroom and is qualified for first-year chemistry labs", "pending"),
    (6, 6, 3, "Assign 32555 second tutorial group (3.0h) to Prof Chloe Davis", 3, "Davis is 6h under threshold and already teaches the subject", "accepted"),
    (7, 7, 6, "Allocate 48023 extra workshop (4.0h) to Dr Farid Hassan", 6, "Hassan is well under a 0.6 expected load", "pending"),
    (8, 8, 9, "Assign admissions interviewing overflow (4.0h) to Dr Isla Murphy", 9, "Murphy has capacity and prior admissions experience", "rejected"),
    (9, 9, 5, "Defer Dr Elena Rossi annual leave by one week", 5, "Avoids overlap with 48620 assessment period", "overridden"),
    (10, 2, 1, "Reschedule Wed research block to 14:00-18:00", 1, "Removes overlap with CB11 tutorial while keeping recurring pattern", "pending"),
    (11, 5, 11, "Reduce NHMRC grant hours from 15.0h to 12.0h this semester", None, "Grant milestone allows a lighter load in S2", "pending"),
]

SEED_DATA = {
    "staff_workload_profile": STAFF_WORKLOAD_PROFILE,
    "workload_entry": WORKLOAD_ENTRY,
    "availability_slot": AVAILABILITY_SLOT,
    "leave_record": LEAVE_RECORD,
    "workload_rule": WORKLOAD_RULE,
    "workload_alert": WORKLOAD_ALERT,
    "rebalance_recommendation": REBALANCE_RECOMMENDATION,
}


def main():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    for table, rows in SEED_DATA.items():
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        cursor.execute(create_table_sql(table))
        columns = list(TABLES[table]["columns"].keys())
        placeholders = ", ".join("?" for _ in columns)
        cursor.executemany(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            rows,
        )
        print(f"  {table}: {len(rows)} records")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_NAME}")


if __name__ == "__main__":
    main()
