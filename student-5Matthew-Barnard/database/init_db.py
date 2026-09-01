import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "performance_dev.db")


def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS PerformanceReviews (
            reviewID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL,
            reviewDate TEXT NOT NULL,
            reviewerID INTEGER NOT NULL,
            rating REAL,
            feedback TEXT,
            status TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS DevelopmentGoals (
            goalID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            targetDate TEXT,
            progress REAL DEFAULT 0,
            status TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS TrainingPrograms (
            trainingID INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            provider TEXT,
            startDate TEXT,
            endDate TEXT,
            skillArea TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS StaffTraining (
            staffTrainingID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL,
            trainingID INTEGER NOT NULL,
            enrolmentDate TEXT,
            completionDate TEXT,
            status TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS DevelopmentRecommendations (
            recommendationID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL,
            goalID INTEGER,
            recommendationType TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            rationale TEXT,
            dateGenerated TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print(f"Database initialized at: {DB_PATH}")
