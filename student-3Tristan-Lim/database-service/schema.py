TABLES = {
    "staff_workload_profile": {
        "pk": "profile_id",
        "columns": {
            "profile_id": "INTEGER PRIMARY KEY",
            "staff_id": "INTEGER NOT NULL",
            "staff_name": "TEXT NOT NULL",
            "department": "TEXT NOT NULL",
            "semester": "TEXT NOT NULL",
            "contracted_fraction": "REAL NOT NULL",   # 1.0 = full time, 0.5 = half
            "max_weekly_hours": "REAL NOT NULL",
            "current_total_hours": "REAL NOT NULL DEFAULT 0",
            "status": "TEXT NOT NULL DEFAULT 'ok'",    # ok | overloaded | underloaded
        },
    },
    "workload_entry": {
        "pk": "entry_id",
        "columns": {
            "entry_id": "INTEGER PRIMARY KEY",
            "staff_id": "INTEGER NOT NULL",
            "activity_type": "TEXT NOT NULL",          # teaching | research | professional_development | service | admin
            "description": "TEXT",
            "hours_per_week": "REAL NOT NULL",
            "start_date": "TEXT NOT NULL",
            "end_date": "TEXT NOT NULL",
            "semester": "TEXT NOT NULL",
            "source_service": "TEXT DEFAULT 'manual'",  # which microservice contributed the hours
        },
    },
    "availability_slot": {
        "pk": "slot_id",
        "columns": {
            "slot_id": "INTEGER PRIMARY KEY",
            "staff_id": "INTEGER NOT NULL",
            "day_of_week": "TEXT NOT NULL",             # Mon..Sun
            "start_time": "TEXT NOT NULL",              # HH:MM (24h)
            "end_time": "TEXT NOT NULL",
            "availability": "TEXT NOT NULL DEFAULT 'available'",  # available | unavailable | preferred
            "is_recurring": "INTEGER NOT NULL DEFAULT 1",
        },
    },
    "leave_record": {
        "pk": "leave_id",
        "columns": {
            "leave_id": "INTEGER PRIMARY KEY",
            "staff_id": "INTEGER NOT NULL",
            "leave_type": "TEXT NOT NULL",              # annual | sick | conference | long_service | parental
            "start_date": "TEXT NOT NULL",
            "end_date": "TEXT NOT NULL",
            "reason": "TEXT",
            "approval": "TEXT NOT NULL DEFAULT 'pending'",  # pending | approved | rejected
        },
    },
    "workload_rule": {
        "pk": "rule_id",
        "columns": {
            "rule_id": "INTEGER PRIMARY KEY",
            "name": "TEXT NOT NULL",
            "applies_to": "TEXT NOT NULL DEFAULT 'all'",  # 'all' or a department name
            "max_total_hours": "REAL NOT NULL",
            "warning_threshold": "REAL NOT NULL",         # hours at which a warning alert is raised
        },
    },
    "workload_alert": {
        "pk": "alert_id",
        "columns": {
            "alert_id": "INTEGER PRIMARY KEY",
            "staff_id": "INTEGER NOT NULL",
            "alert_type": "TEXT NOT NULL",               # overload | underload | clash
            "severity": "TEXT NOT NULL DEFAULT 'medium'",  # low | medium | high
            "message": "TEXT NOT NULL",
            "status": "TEXT NOT NULL DEFAULT 'open'",     # open | acknowledged | resolved
            "date_raised": "TEXT NOT NULL",
        },
    },
    "rebalance_recommendation": {
        "pk": "rec_id",
        "columns": {
            "rec_id": "INTEGER PRIMARY KEY",
            "alert_id": "INTEGER",
            "staff_id": "INTEGER NOT NULL",
            "suggested_action": "TEXT NOT NULL",
            "target_staff_id": "INTEGER",                 # staff the work would move to
            "rationale": "TEXT",
            "decision_status": "TEXT NOT NULL DEFAULT 'pending'",  # pending | accepted | rejected | overridden
        },
    },
}


def create_table_sql(table):
    spec = TABLES[table]
    cols = ",\n    ".join(f"{name} {sql}" for name, sql in spec["columns"].items())
    return f"CREATE TABLE IF NOT EXISTS {table} (\n    {cols}\n)"


def column_names(table, include_pk=True):
    spec = TABLES[table]
    return [c for c in spec["columns"] if include_pk or c != spec["pk"]]
