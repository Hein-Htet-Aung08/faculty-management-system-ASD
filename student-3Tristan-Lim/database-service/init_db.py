import os
import sqlite3

from schema import TABLES, create_table_sql

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
DATABASE_NAME = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "workload.db"))

os.makedirs(os.path.dirname(DATABASE_NAME) or ".", exist_ok=True)

SEMESTER = "2026-S2"

# --------------------------------------------------------------------- seeds ---

# staff_id, name and department match the Student 1 roster exactly.
STAFF_WORKLOAD_PROFILE = [
    # profile_id, staff_id, staff_name, department, semester, contracted_fraction,
    # max_weekly_hours, current_total_hours, status
    (1, 1, "John Smith", "Computer Science", SEMESTER, 1.0, 37.5, 41.0, "overloaded"),
    (2, 2, "Grace Tan", "Computer Science", SEMESTER, 1.0, 37.5, 36.0, "ok"),
    (3, 3, "Marcus Chen", "Information Technology", SEMESTER, 1.0, 37.5, 21.0, "underloaded"),
    (4, 4, "Priya Nair", "Information Technology", SEMESTER, 0.5, 18.75, 20.0, "overloaded"),
    (5, 5, "David Kim", "Mechanical Engineering", SEMESTER, 1.0, 37.5, 33.0, "ok"),
    (6, 6, "Fatima Ali", "Accounting", SEMESTER, 1.0, 37.5, 12.0, "underloaded"),
    (7, 7, "Ben Robertson", "Marketing", SEMESTER, 1.0, 37.5, 37.0, "ok"),
    (8, 8, "Hana Suzuki", "Management", SEMESTER, 0.5, 18.75, 20.0, "overloaded"),
    (9, 9, "Carlos Mendes", "Nursing", SEMESTER, 1.0, 37.5, 28.0, "underloaded"),
    (10, 10, "Olivia Bennett", "Psychology", SEMESTER, 1.0, 37.5, 37.5, "ok"),
]

WORKLOAD_ENTRY = [
    # entry_id, staff_id, activity_type, description, hours_per_week,
    # start_date, end_date, semester, source_service
    (1, 1, "teaching", "31266 Introduction to Software Development", 14.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (2, 1, "teaching", "48024 Programming Fundamentals tutorials", 9.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (3, 1, "research", "ARC Discovery grant - agentic systems", 12.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (4, 1, "service", "Course coordination - Bachelor of IT", 6.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (5, 2, "teaching", "31251 Advanced Programming", 16.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (6, 2, "professional_development", "Learning and teaching micro-credential", 4.0, "2026-08-01", "2026-10-30", SEMESTER, "performance-dev"),
    (7, 2, "admin", "Timetabling working group", 16.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (8, 3, "teaching", "31268 Web Systems", 11.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (9, 3, "research", "Supervision - 3 HDR candidates", 10.0, "2026-07-01", "2026-12-15", SEMESTER, "research-grant"),
    (10, 4, "teaching", "32555 Fundamentals of Interaction Design", 14.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (11, 4, "research", "Industry usability study", 6.0, "2026-08-01", "2026-11-30", SEMESTER, "research-grant"),
    (12, 5, "teaching", "48620 Engineering Mechanics", 20.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (13, 5, "professional_development", "WHS refresher training", 3.0, "2026-08-10", "2026-08-24", SEMESTER, "performance-dev"),
    (14, 5, "admin", "Lab safety officer", 10.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (15, 6, "teaching", "22107 Accounting for Business Decisions", 12.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (16, 7, "teaching", "24108 Marketing Foundations", 22.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (17, 7, "service", "Admissions interviewer", 15.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (18, 8, "teaching", "21129 Managing People and Organisations", 14.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (19, 8, "research", "Case study authoring", 6.0, "2026-08-01", "2026-11-30", SEMESTER, "research-grant"),
    (20, 9, "teaching", "92418 Clinical Practice", 16.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (21, 9, "professional_development", "Clinical supervision workshop", 4.0, "2026-09-01", "2026-09-30", SEMESTER, "performance-dev"),
    (22, 9, "service", "Placement coordination", 8.0, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
    (23, 10, "teaching", "92552 Foundations of Psychology", 21.0, "2026-07-28", "2026-11-06", SEMESTER, "teaching-allocation"),
    (24, 10, "service", "Ethics committee member", 16.5, "2026-07-01", "2026-12-15", SEMESTER, "manual"),
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
    (17, 10, "Thu", "12:00", "18:00", "preferred", 1),
]

LEAVE_RECORD = [
    # leave_id, staff_id, leave_type, start_date, end_date, reason, approval
    (1, 1, "conference", "2026-09-14", "2026-09-18", "ICSE presentation", "approved"),
    (2, 3, "long_service", "2026-10-05", "2026-10-30", "Long service leave block", "approved"),
    (3, 4, "sick", "2026-08-24", "2026-08-26", "Medical certificate provided", "approved"),
    (4, 5, "annual", "2026-09-28", "2026-10-02", "Family holiday", "pending"),
    (5, 5, "long_service", "2026-08-01", "2026-12-15", "Recorded as On Leave in the staff service", "approved"),
    (6, 6, "conference", "2026-11-02", "2026-11-06", "Accounting educators symposium", "pending"),
    (7, 7, "annual", "2026-09-21", "2026-09-25", "Annual leave", "approved"),
    (8, 8, "sick", "2026-08-18", "2026-08-19", "Short illness", "approved"),
    (9, 9, "annual", "2026-10-12", "2026-10-16", "Annual leave", "rejected"),
    (10, 9, "conference", "2026-09-07", "2026-09-11", "Nursing practice congress", "approved"),
    (11, 10, "annual", "2026-11-09", "2026-11-13", "Annual leave", "pending"),
]

# applies_to matches the department names used by the staff service.
WORKLOAD_RULE = [
    # rule_id, name, applies_to, max_total_hours, warning_threshold
    (1, "University standard full-time cap", "all", 37.5, 34.0),
    (2, "Computer Science cap", "Computer Science", 38.0, 34.0),
    (3, "Information Technology cap", "Information Technology", 38.0, 34.0),
    (4, "Mechanical Engineering cap", "Mechanical Engineering", 38.0, 34.0),
    (5, "Accounting cap", "Accounting", 37.5, 34.0),
    (6, "Marketing cap", "Marketing", 37.5, 34.0),
    (7, "Management cap", "Management", 37.5, 33.0),
    (8, "Nursing cap", "Nursing", 38.0, 34.0),
    (9, "Psychology cap", "Psychology", 37.5, 34.0),
    (10, "Teaching activity soft cap", "all", 24.0, 20.0),
    (11, "Admin and service soft cap", "all", 16.0, 12.0),
]

WORKLOAD_ALERT = [
    # alert_id, staff_id, alert_type, severity, message, status, date_raised
    (1, 1, "overload", "high", "Total 41.0h exceeds cap 37.5h for Computer Science", "open", "2026-08-20"),
    (2, 1, "clash", "medium", "Conference leave overlaps 31266 teaching weeks", "open", "2026-08-20"),
    (3, 4, "overload", "medium", "Total 20.0h exceeds 0.5 fractional cap 18.75h", "open", "2026-08-20"),
    (4, 8, "overload", "medium", "Total 20.0h exceeds 0.5 fractional cap 18.75h", "acknowledged", "2026-08-19"),
    (5, 3, "underload", "low", "Total 21.0h below underload floor 30.0h", "open", "2026-08-21"),
    (6, 6, "underload", "medium", "Total 12.0h below underload floor 30.0h", "open", "2026-08-21"),
    (7, 9, "underload", "low", "Total 28.0h below underload floor 30.0h", "open", "2026-08-21"),
    (8, 5, "clash", "medium", "Requested annual leave overlaps 48620 teaching weeks", "open", "2026-08-22"),
    (9, 7, "clash", "low", "Annual leave overlaps 24108 teaching weeks", "open", "2026-08-22"),
    (10, 10, "overload", "low", "Total 37.5h is at cap 37.5h - no headroom", "acknowledged", "2026-08-22"),
    (11, 2, "clash", "low", "Admin load 16.0h sits at the service soft cap", "resolved", "2026-08-23"),
]

REBALANCE_RECOMMENDATION = [
    # rec_id, alert_id, staff_id, suggested_action, target_staff_id, rationale, decision_status
    (1, 1, 1, "Move 48024 tutorials (9.0h) to Marcus Chen", 3, "Chen has 16.5h headroom and teaches adjacent IT subjects", "pending"),
    (2, 1, 1, "Reduce course coordination from 6.0h to 3.0h", None, "Coordination is above the admin soft cap for a research-active staff member", "pending"),
    (3, 1, 1, "Transfer ARC grant supervision (12.0h) partly to Fatima Ali", 6, "Ali is at 12.0h with substantial headroom this semester", "pending"),
    (4, 3, 4, "Shift industry usability study (6.0h) to next semester", None, "Task is not time-critical and staff is on a 0.5 fraction", "accepted"),
    (5, 4, 8, "Move case study authoring (6.0h) to Carlos Mendes", 9, "Mendes has 9.5h headroom before the underload floor", "pending"),
    (6, 5, 3, "Assign 31268 second tutorial group (3.0h) to Marcus Chen", 3, "Chen is well under the underload floor and already teaches the subject", "accepted"),
    (7, 6, 6, "Allocate 22107 extra workshop (4.0h) to Fatima Ali", 6, "Ali is 18h under a full-time expected load", "pending"),
    (8, 7, 9, "Assign placement coordination overflow (4.0h) to Carlos Mendes", 9, "Mendes has capacity and prior placement experience", "rejected"),
    (9, 8, 5, "Defer David Kim annual leave by one week", 5, "Avoids overlap with 48620 assessment period", "overridden"),
    (10, 2, 1, "Reschedule Wed research block to 14:00-18:00", 1, "Removes overlap with the Wed tutorial while keeping the recurring pattern", "pending"),
    (11, 10, 10, "Reduce ethics committee load from 16.5h to 12.0h", None, "Service load sits above the admin soft cap", "pending"),
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
