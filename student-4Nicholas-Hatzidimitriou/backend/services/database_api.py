import os
import sqlite3
 
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
DB_FILE = os.path.join(DATA_DIR, "student4.db")
 
 
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
# ResearchProjects
def list_projects(department=None, status=None):
    query = "SELECT * FROM ResearchProjects WHERE 1=1"
    params = []
    if department:
        query += " AND department = ?"
        params.append(department)
    if status:
        query += " AND status = ?"
        params.append(status)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_project(project_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    conn.close()
    return row
 
 
def project_exists(project_id):
    conn = get_db()
    row = conn.execute(
        "SELECT projectID FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    conn.close()
    return row is not None
 
 
def create_project(data):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO ResearchProjects (title, description, department, status, startDate, endDate, leadStaffID)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["title"],
            data.get("description"),
            data["department"],
            data["status"],
            data.get("startDate"),
            data.get("endDate"),
            data.get("leadStaffID"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_project(project_id, data):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE ResearchProjects
        SET title = ?, description = ?, department = ?, status = ?,
            startDate = ?, endDate = ?, leadStaffID = ?
        WHERE projectID = ?
        """,
        (
            data.get("title", existing["title"]),
            data.get("description", existing["description"]),
            data.get("department", existing["department"]),
            data.get("status", existing["status"]),
            data.get("startDate", existing["startDate"]),
            data.get("endDate", existing["endDate"]),
            data.get("leadStaffID", existing["leadStaffID"]),
            project_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_project(project_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM ResearchProjects WHERE projectID = ?", (project_id,))
    conn.commit()
    conn.close()
    return True
 
# Grants
def list_grants(status=None, project_id=None):
    query = "SELECT * FROM Grants WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if project_id:
        query += " AND projectID = ?"
        params.append(project_id)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_grant(grant_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    conn.close()
    return row
 
 
def grant_exists(grant_id):
    conn = get_db()
    row = conn.execute("SELECT grantID FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    conn.close()
    return row is not None
 
 
def create_grant(data):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO Grants (projectID, fundingBody, amountRequested, amountAwarded, applicationDeadline, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["projectID"],
            data["fundingBody"],
            data["amountRequested"],
            data.get("amountAwarded"),
            data["applicationDeadline"],
            data["status"],
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_grant(grant_id, data):
    conn = get_db()
    existing = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE Grants
        SET projectID = ?, fundingBody = ?, amountRequested = ?, amountAwarded = ?,
            applicationDeadline = ?, status = ?
        WHERE grantID = ?
        """,
        (
            data.get("projectID", existing["projectID"]),
            data.get("fundingBody", existing["fundingBody"]),
            data.get("amountRequested", existing["amountRequested"]),
            data.get("amountAwarded", existing["amountAwarded"]),
            data.get("applicationDeadline", existing["applicationDeadline"]),
            data.get("status", existing["status"]),
            grant_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_grant(grant_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM Grants WHERE grantID = ?", (grant_id,))
    conn.commit()
    conn.close()
    return True
 
# Publications
def list_publications(project_id=None, staff_id=None, publication_type=None):
    query = "SELECT * FROM Publications WHERE 1=1"
    params = []
    if project_id:
        query += " AND projectID = ?"
        params.append(project_id)
    if staff_id:
        query += " AND staffID = ?"
        params.append(staff_id)
    if publication_type:
        query += " AND publicationType = ?"
        params.append(publication_type)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_publication(publication_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    conn.close()
    return row
 
 
def create_publication(data):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO Publications (projectID, staffID, title, publicationType, journalOrVenue, datePublished)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["projectID"],
            data.get("staffID"),
            data["title"],
            data["publicationType"],
            data.get("journalOrVenue"),
            data.get("datePublished"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_publication(publication_id, data):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE Publications
        SET projectID = ?, staffID = ?, title = ?, publicationType = ?,
            journalOrVenue = ?, datePublished = ?
        WHERE publicationID = ?
        """,
        (
            data.get("projectID", existing["projectID"]),
            data.get("staffID", existing["staffID"]),
            data.get("title", existing["title"]),
            data.get("publicationType", existing["publicationType"]),
            data.get("journalOrVenue", existing["journalOrVenue"]),
            data.get("datePublished", existing["datePublished"]),
            publication_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_publication(publication_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM Publications WHERE publicationID = ?", (publication_id,))
    conn.commit()
    conn.close()
    return True
 
 # ProjectStaff
def list_project_staff(project_id=None, staff_id=None):
    query = "SELECT * FROM ProjectStaff WHERE 1=1"
    params = []
    if project_id:
        query += " AND projectID = ?"
        params.append(project_id)
    if staff_id:
        query += " AND staffID = ?"
        params.append(staff_id)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_project_staff_entry(project_staff_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    conn.close()
    return row
 
 
def create_project_staff(data):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO ProjectStaff (projectID, staffID, role) VALUES (?, ?, ?)",
        (data["projectID"], data["staffID"], data["role"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_project_staff(project_staff_id, data):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE ProjectStaff
        SET projectID = ?, staffID = ?, role = ?
        WHERE projectStaffID = ?
        """,
        (
            data.get("projectID", existing["projectID"]),
            data.get("staffID", existing["staffID"]),
            data.get("role", existing["role"]),
            project_staff_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_project_staff(project_staff_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,))
    conn.commit()
    conn.close()
    return True
 
 
# GrantAlerts
def list_grant_alerts(grant_id=None, status=None):
    query = "SELECT * FROM GrantAlerts WHERE 1=1"
    params = []
    if grant_id:
        query += " AND grantID = ?"
        params.append(grant_id)
    if status:
        query += " AND status = ?"
        params.append(status)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_grant_alert(alert_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    conn.close()
    return row
 
 
def create_grant_alert(data):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO GrantAlerts (grantID, alertType, dueDate, status)
        VALUES (?, ?, ?, ?)
        """,
        (data["grantID"], data["alertType"], data["dueDate"], data["status"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_grant_alert(alert_id, data):
    conn = get_db()
    existing = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE GrantAlerts
        SET grantID = ?, alertType = ?, dueDate = ?, status = ?
        WHERE alertID = ?
        """,
        (
            data.get("grantID", existing["grantID"]),
            data.get("alertType", existing["alertType"]),
            data.get("dueDate", existing["dueDate"]),
            data.get("status", existing["status"]),
            alert_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_grant_alert(alert_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM GrantAlerts WHERE alertID = ?", (alert_id,))
    conn.commit()
    conn.close()
    return True
 

# ResearchAIAnalysis
def list_ai_analyses(project_id=None, staff_id=None):
    query = "SELECT * FROM ResearchAIAnalysis WHERE 1=1"
    params = []
    if project_id:
        query += " AND projectID = ?"
        params.append(project_id)
    if staff_id:
        query += " AND staffID = ?"
        params.append(staff_id)
 
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows
 
 
def get_ai_analysis(analysis_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    return row
 
 
def create_ai_analysis(data):
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO ResearchAIAnalysis
            (projectID, staffID, generatedSummary, recommendedStaffMatches, matchRationale)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.get("projectID"),
            data.get("staffID"),
            data.get("generatedSummary"),
            data.get("recommendedStaffMatches"),
            data.get("matchRationale"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id
 
 
def update_ai_analysis(analysis_id, data):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute(
        """
        UPDATE ResearchAIAnalysis
        SET projectID = ?, staffID = ?, generatedSummary = ?,
            recommendedStaffMatches = ?, matchRationale = ?
        WHERE analysisID = ?
        """,
        (
            data.get("projectID", existing["projectID"]),
            data.get("staffID", existing["staffID"]),
            data.get("generatedSummary", existing["generatedSummary"]),
            data.get("recommendedStaffMatches", existing["recommendedStaffMatches"]),
            data.get("matchRationale", existing["matchRationale"]),
            analysis_id,
        ),
    )
    conn.commit()
    conn.close()
    return True
 
 
def delete_ai_analysis(analysis_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return False
 
    conn.execute("DELETE FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,))
    conn.commit()
    conn.close()
    return True