import sqlite3
import os
from pathlib import Path

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
DB_FILE = Path(DATA_DIR) / "student4.db"

os.makedirs(DATA_DIR, exist_ok=True)

conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ResearchProjects (
    projectID     INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    description   TEXT,
    department    TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('proposed', 'in progress', 'completed', 'on hold')),
    startDate     DATE,
    endDate       DATE,
    leadStaffID   INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Grants (
    grantID             INTEGER PRIMARY KEY AUTOINCREMENT,
    projectID           INTEGER NOT NULL,
    fundingBody         TEXT NOT NULL,
    amountRequested     REAL NOT NULL,
    amountAwarded       REAL,
    applicationDeadline DATE NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('applied', 'rejected', 'awarded', 'completed', 'in progress')),
    FOREIGN KEY (projectID) REFERENCES ResearchProjects(projectID)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Publications (
    publicationID    INTEGER PRIMARY KEY AUTOINCREMENT,
    projectID        INTEGER NOT NULL,
    staffID          INTEGER,
    title            TEXT NOT NULL,
    publicationType  TEXT NOT NULL CHECK (publicationType IN ('journal', 'conference', 'book chapter', 'report')),
    journalOrVenue   TEXT,
    datePublished    DATE,
    FOREIGN KEY (projectID) REFERENCES ResearchProjects(projectID)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ProjectStaff (
    projectStaffID  INTEGER PRIMARY KEY AUTOINCREMENT,
    projectID       INTEGER NOT NULL,
    staffID         INTEGER NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('lead', 'co-investigator', 'research assistant', 'contributor')),
    FOREIGN KEY (projectID) REFERENCES ResearchProjects(projectID)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS GrantAlerts (
    alertID    INTEGER PRIMARY KEY AUTOINCREMENT,
    grantID    INTEGER NOT NULL,
    alertType  TEXT NOT NULL CHECK (alertType IN ('deadline approaching', 'missing documents', 'status change', 'overdue')),
    dueDate    DATE NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('active', 'dismissed', 'resolved')),
    FOREIGN KEY (grantID) REFERENCES Grants(grantID)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ResearchAIAnalysis (
    analysisID               INTEGER PRIMARY KEY AUTOINCREMENT,
    projectID                INTEGER,
    staffID                  INTEGER,
    generatedSummary         TEXT,
    recommendedStaffMatches  TEXT,
    matchRationale           TEXT,
    dateGenerated            DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (projectID) REFERENCES ResearchProjects(projectID)
)
""")

conn.commit()
conn.close()