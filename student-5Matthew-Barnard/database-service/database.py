import os
import sqlite3
from pathlib import Path

from schema import create_schema
from seed_data import SEED_DATA

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "data" / "performance_dev.db"

SEED_COLUMNS = {
    "PerformanceReviews": (
        "reviewID", "staffID", "reviewDate", "reviewerID", "rating", "feedback", "status"
    ),
    "DevelopmentGoals": (
        "goalID", "staffID", "title", "description", "targetDate", "progress", "status"
    ),
    "TrainingPrograms": (
        "trainingID", "title", "description", "provider", "startDate", "endDate", "skillArea"
    ),
    "StaffTraining": (
        "staffTrainingID", "staffID", "trainingID", "enrolmentDate", "completionDate", "status"
    ),
    "DevelopmentRecommendations": (
        "recommendationID", "staffID", "goalID", "recommendationType",
        "recommendation", "rationale", "dateGenerated", "status"
    ),
}


def database_path():
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)))


def get_connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(seed=True):
    """Create missing tables and add only missing sample rows."""
    connection = get_connection()
    try:
        create_schema(connection)
        if seed:
            for table, rows in SEED_DATA.items():
                columns = SEED_COLUMNS[table]
                placeholders = ", ".join("?" for _ in columns)
                connection.executemany(
                    f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) "
                    f"VALUES ({placeholders})",
                    rows,
                )
        connection.commit()
    finally:
        connection.close()


def table_counts():
    connection = get_connection()
    try:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in SEED_DATA
        }
    finally:
        connection.close()
