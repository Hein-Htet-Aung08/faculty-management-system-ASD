import os
import sqlite3
from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
DB_FILE = os.path.join(DATA_DIR, "student4.db")
 
 
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
def rows_to_list(rows):
    return [dict(r) for r in rows]
 
 
def row_to_dict(row):
    return dict(row) if row else None
 
 
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "database-service"}), 200
 
# ResearchProjects
@app.route("/projects", methods=["GET"])
def list_projects():
    department = request.args.get("department")
    status = request.args.get("status")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json()
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
    return jsonify({"projectID": new_id}), 201
 
 
@app.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Project not found"}), 404
 
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
    return jsonify({"message": "Project updated"}), 200
 
 
@app.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchProjects WHERE projectID = ?", (project_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Project not found"}), 404
    conn.execute("DELETE FROM ResearchProjects WHERE projectID = ?", (project_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Project deleted"}), 200
 
# Grants
@app.route("/grants", methods=["GET"])
def list_grants():
    status = request.args.get("status")
    project_id = request.args.get("projectID")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/grants/<int:grant_id>", methods=["GET"])
def get_grant(grant_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Grant not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/grants", methods=["POST"])
def create_grant():
    data = request.get_json()
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
    return jsonify({"grantID": new_id}), 201
 
 
@app.route("/grants/<int:grant_id>", methods=["PUT"])
def update_grant(grant_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Grant not found"}), 404
 
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
    return jsonify({"message": "Grant updated"}), 200
 
 
@app.route("/grants/<int:grant_id>", methods=["DELETE"])
def delete_grant(grant_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM Grants WHERE grantID = ?", (grant_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Grant not found"}), 404
    conn.execute("DELETE FROM Grants WHERE grantID = ?", (grant_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Grant deleted"}), 200
 
# Publications
@app.route("/publications", methods=["GET"])
def list_publications():
    project_id = request.args.get("projectID")
    staff_id = request.args.get("staffID")
    publication_type = request.args.get("publicationType")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/publications/<int:publication_id>", methods=["GET"])
def get_publication(publication_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Publication not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/publications", methods=["POST"])
def create_publication():
    data = request.get_json()
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
    return jsonify({"publicationID": new_id}), 201
 
 
@app.route("/publications/<int:publication_id>", methods=["PUT"])
def update_publication(publication_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Publication not found"}), 404
 
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
    return jsonify({"message": "Publication updated"}), 200
 
 
@app.route("/publications/<int:publication_id>", methods=["DELETE"])
def delete_publication(publication_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM Publications WHERE publicationID = ?", (publication_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Publication not found"}), 404
    conn.execute("DELETE FROM Publications WHERE publicationID = ?", (publication_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Publication deleted"}), 200
 
# ProjectStaff
@app.route("/project-staff", methods=["GET"])
def list_project_staff():
    project_id = request.args.get("projectID")
    staff_id = request.args.get("staffID")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/project-staff/<int:project_staff_id>", methods=["GET"])
def get_project_staff_entry(project_staff_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "ProjectStaff entry not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/project-staff", methods=["POST"])
def create_project_staff():
    data = request.get_json()
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO ProjectStaff (projectID, staffID, role) VALUES (?, ?, ?)",
        (data["projectID"], data["staffID"], data["role"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"projectStaffID": new_id}), 201
 
 
@app.route("/project-staff/<int:project_staff_id>", methods=["PUT"])
def update_project_staff(project_staff_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "ProjectStaff entry not found"}), 404
 
    conn.execute(
        "UPDATE ProjectStaff SET projectID = ?, staffID = ?, role = ? WHERE projectStaffID = ?",
        (
            data.get("projectID", existing["projectID"]),
            data.get("staffID", existing["staffID"]),
            data.get("role", existing["role"]),
            project_staff_id,
        ),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "ProjectStaff entry updated"}), 200
 
 
@app.route("/project-staff/<int:project_staff_id>", methods=["DELETE"])
def delete_project_staff(project_staff_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "ProjectStaff entry not found"}), 404
    conn.execute("DELETE FROM ProjectStaff WHERE projectStaffID = ?", (project_staff_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "ProjectStaff entry deleted"}), 200
 
# GrantAlerts
@app.route("/grant-alerts", methods=["GET"])
def list_grant_alerts():
    grant_id = request.args.get("grantID")
    status = request.args.get("status")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/grant-alerts/<int:alert_id>", methods=["GET"])
def get_grant_alert(alert_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "Grant alert not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/grant-alerts", methods=["POST"])
def create_grant_alert():
    data = request.get_json()
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO GrantAlerts (grantID, alertType, dueDate, status) VALUES (?, ?, ?, ?)",
        (data["grantID"], data["alertType"], data["dueDate"], data["status"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"alertID": new_id}), 201
 
 
@app.route("/grant-alerts/<int:alert_id>", methods=["PUT"])
def update_grant_alert(alert_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Grant alert not found"}), 404
 
    conn.execute(
        "UPDATE GrantAlerts SET grantID = ?, alertType = ?, dueDate = ?, status = ? WHERE alertID = ?",
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
    return jsonify({"message": "Grant alert updated"}), 200
 
 
@app.route("/grant-alerts/<int:alert_id>", methods=["DELETE"])
def delete_grant_alert(alert_id):
    conn = get_db()
    existing = conn.execute("SELECT * FROM GrantAlerts WHERE alertID = ?", (alert_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Grant alert not found"}), 404
    conn.execute("DELETE FROM GrantAlerts WHERE alertID = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Grant alert deleted"}), 200
 
# ResearchAIAnalysis
@app.route("/ai-analysis", methods=["GET"])
def list_ai_analyses():
    project_id = request.args.get("projectID")
    staff_id = request.args.get("staffID")
 
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
    return jsonify(rows_to_list(rows)), 200
 
 
@app.route("/ai-analysis/<int:analysis_id>", methods=["GET"])
def get_ai_analysis(analysis_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "AI analysis record not found"}), 404
    return jsonify(row_to_dict(row)), 200
 
 
@app.route("/ai-analysis", methods=["POST"])
def create_ai_analysis():
    data = request.get_json()
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
    return jsonify({"analysisID": new_id}), 201
 
 
@app.route("/ai-analysis/<int:analysis_id>", methods=["PUT"])
def update_ai_analysis(analysis_id):
    data = request.get_json()
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "AI analysis record not found"}), 404
 
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
    return jsonify({"message": "AI analysis record updated"}), 200
 
 
@app.route("/ai-analysis/<int:analysis_id>", methods=["DELETE"])
def delete_ai_analysis(analysis_id):
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,)
    ).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "AI analysis record not found"}), 404
    conn.execute("DELETE FROM ResearchAIAnalysis WHERE analysisID = ?", (analysis_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "AI analysis record deleted"}), 200
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5104)), debug=True)