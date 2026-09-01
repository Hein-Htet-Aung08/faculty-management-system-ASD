import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "performance_dev.db")


def seed_sample_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today().isoformat()

    cursor.execute(
        """
        INSERT OR IGNORE INTO PerformanceReviews (staffID, reviewDate, reviewerID, rating, feedback, status)
        VALUES (101, ?, 201, 4.5, 'Strong performance with good leadership contributions.', 'Completed')
        """,
        (today,)
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO DevelopmentGoals (staffID, title, description, targetDate, progress, status)
        VALUES (101, 'Leadership Growth', 'Develop people management and mentoring capabilities.', ?, 35.0, 'In Progress')
        """,
        (today,)
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO TrainingPrograms (title, description, provider, startDate, endDate, skillArea)
        VALUES ('Introduction to Coaching', 'Foundational coaching skills for managers.', 'UTS Learning Hub', ?, ?, 'Leadership')
        """,
        (today, today)
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO StaffTraining (staffID, trainingID, enrolmentDate, completionDate, status)
        VALUES (101, 1, ?, NULL, 'Enrolled')
        """,
        (today,)
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO DevelopmentRecommendations (staffID, goalID, recommendationType, recommendation, rationale, dateGenerated, status)
        VALUES (101, 1, 'Training', 'Enroll in advanced coaching workshop.', 'Improves mentoring and team leadership capability.', ?, 'Active')
        """,
        (today,)
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed_sample_data()
    print(f"Sample data inserted into: {DB_PATH}")
