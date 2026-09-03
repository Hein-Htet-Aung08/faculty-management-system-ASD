TABLES = {
    "PerformanceReviews": """
        CREATE TABLE IF NOT EXISTS PerformanceReviews (
            reviewID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL CHECK (staffID > 0),
            reviewDate TEXT NOT NULL,
            reviewerID INTEGER NOT NULL CHECK (reviewerID > 0),
            rating REAL CHECK (rating BETWEEN 1 AND 5),
            feedback TEXT,
            status TEXT NOT NULL CHECK (
                status IN ('Draft', 'Scheduled', 'Completed', 'Acknowledged')
            )
        )
    """,
    "DevelopmentGoals": """
        CREATE TABLE IF NOT EXISTS DevelopmentGoals (
            goalID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL CHECK (staffID > 0),
            title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 120),
            description TEXT,
            targetDate TEXT,
            progress REAL NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
            status TEXT NOT NULL CHECK (
                status IN ('Planned', 'In Progress', 'Completed', 'On Hold', 'Cancelled')
            )
        )
    """,
    "TrainingPrograms": """
        CREATE TABLE IF NOT EXISTS TrainingPrograms (
            trainingID INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 160),
            description TEXT,
            provider TEXT,
            startDate TEXT,
            endDate TEXT,
            skillArea TEXT,
            CHECK (endDate IS NULL OR startDate IS NULL OR endDate >= startDate)
        )
    """,
    "StaffTraining": """
        CREATE TABLE IF NOT EXISTS StaffTraining (
            staffTrainingID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL CHECK (staffID > 0),
            trainingID INTEGER NOT NULL,
            enrolmentDate TEXT,
            completionDate TEXT,
            status TEXT NOT NULL CHECK (
                status IN ('Enrolled', 'In Progress', 'Completed', 'Withdrawn')
            ),
            FOREIGN KEY (trainingID) REFERENCES TrainingPrograms(trainingID)
                ON UPDATE CASCADE ON DELETE RESTRICT,
            UNIQUE (staffID, trainingID)
        )
    """,
    "DevelopmentRecommendations": """
        CREATE TABLE IF NOT EXISTS DevelopmentRecommendations (
            recommendationID INTEGER PRIMARY KEY AUTOINCREMENT,
            staffID INTEGER NOT NULL CHECK (staffID > 0),
            goalID INTEGER,
            recommendationType TEXT NOT NULL CHECK (
                recommendationType IN ('Training', 'Goal', 'Mentoring', 'Experience')
            ),
            recommendation TEXT NOT NULL,
            rationale TEXT,
            dateGenerated TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('Pending', 'Accepted', 'Rejected', 'Modified')
            ),
            FOREIGN KEY (goalID) REFERENCES DevelopmentGoals(goalID)
                ON UPDATE CASCADE ON DELETE SET NULL
        )
    """,
}


def create_schema(connection):
    """Create every registered table in dependency-safe insertion order."""
    for statement in TABLES.values():
        connection.execute(statement)
