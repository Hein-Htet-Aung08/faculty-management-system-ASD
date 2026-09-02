from flask import Flask, jsonify, request
from llm_client import generate_response
from flask_cors import CORS
from datetime import date
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

DATA_DIR = os.getenv("DB_PATH", str(Path(__file__).parent.parent / "database" / "staff.db"))
PROMPT_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename):
    return (PROMPT_DIR / filename).read_text(encoding="utf-8").strip()

def get_db_connection():
    conn = sqlite3.connect(DATA_DIR)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@app.route("/api/staff")
def get_all_staff():
    conn = get_db_connection()
    staff = conn.execute(
        """SELECT staff.staff_id, staff.name, departments.department_name, staff.position, staff.employment_type, staff.status, staff_expertise.expertise_area
        FROM staff
        JOIN departments ON staff.department_id = departments.department_id
        LEFT JOIN staff_expertise ON staff.staff_id = staff_expertise.staff_id"""
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in staff])

@app.route("/api/staff/<int:staff_id>")
def get_staff_by_id(staff_id):
    conn = get_db_connection()
    staff = conn.execute(
        """SELECT staff.staff_id, staff.name, staff.email, staff.phone, staff.department_id, departments.department_name, staff.position, staff.employment_type, staff.status
        FROM staff
        JOIN departments ON staff.department_id = departments.department_id
        WHERE staff.staff_id=?""", (staff_id,)
    ).fetchone()
    conn.close()

    if staff is None:
        return jsonify({"error": "Staff member not found"}), 404
    return jsonify(dict(staff))

@app.route("/api/staff", methods=["POST"])
def create_staff():
    data = request.json
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """INSERT INTO staff (name, email, phone, department_id, position, employment_type, status)
            VALUES (? ,?, ?, ?, ?, ?, ?)""",
            (data["name"], data["email"], data["phone"], data["department_id"], data["position"], data["employment_type"], data["status"])
        )
        new_staff_id = cursor.lastrowid
        
        conn.execute(
            """INSERT INTO staff_expertise (staff_id, expertise_area, skill_level)
            VALUES (?, ?, ?)""",
            (new_staff_id, data["expertise_area"], data["skill_level"])
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Staff member created", "staff_id": new_staff_id}), 201

    except KeyError as e:
        conn.close()
        return jsonify({"error": f"Missing required field: {e}"}), 400

    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": f"Invalid data {e}"}), 400

@app.route("/api/staff/<int:staff_id>", methods=["PUT"])
def update_staff(staff_id):
    data = request.json
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """UPDATE staff
            SET name=?, email=?, phone=?, department_id=?, position=?, employment_type=?, status=?
            WHERE staff_id=?""", 
            (data["name"], data["email"], data["phone"], data["department_id"], data["position"], data["employment_type"], data["status"], staff_id)
        )

        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Staff member not found"}), 404

        conn.close()
        return jsonify({"message": "Staff member updated"}), 200

    except KeyError as e:
        conn.close()
        return jsonify({"error": f"Missing required field: {e}"}), 400

    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": f"Invalid data: {e}"}), 400

@app.route("/api/staff/<int:staff_id>", methods=["DELETE"])
def delete_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.execute(
        """DELETE FROM staff 
        WHERE staff_id=?""", 
        (staff_id,))
        
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404

    conn.close()
    return jsonify({"message": "Staff member deleted"}), 200

@app.route("/api/staff/<int:staff_id>/qualifications")
def get_staff_qualifications(staff_id):
    conn = get_db_connection()
    staff_exists = conn.execute(
        """SELECT staff_id FROM staff WHERE staff_id=?""", (staff_id,)
    ).fetchone()

    if staff_exists is None:
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404

    qualifications = conn.execute(
        """SELECT qualification_id, qualification_name, institution, year_obtained
        FROM staff_qualifications
        WHERE staff_id=?""", (staff_id,)
    ).fetchall()

    conn.close()
    return jsonify([dict(row) for row in qualifications])

@app.route("/api/staff/<int:staff_id>/expertise")
def get_staff_expertise(staff_id):
    conn = get_db_connection()
    staff_exists = conn.execute(
        """SELECT staff_id FROM staff WHERE staff_id=?""", (staff_id,)
    ).fetchone()

    if staff_exists is None:
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404

    expertise = conn.execute(
        """SELECT expertise_id, expertise_area, skill_level
        FROM staff_expertise
        WHERE staff_id=?""", (staff_id,)
    ).fetchall()

    conn.close()
    return jsonify([dict(row) for row in expertise])

@app.route("/api/staff/<int:staff_id>/availability")
def get_staff_availability(staff_id):
    conn = get_db_connection()
    staff_exists = conn.execute(
        """SELECT staff_id FROM staff WHERE staff_id=?""", (staff_id,)
    ).fetchone()

    if staff_exists is None:
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404

    availability = conn.execute(
        """SELECT availability_id, day, time_slot, availability_status
        FROM staff_availability
        WHERE staff_id=?""", (staff_id,)
    ).fetchall()

    conn.close()
    return jsonify([dict(row) for row in availability])

@app.route("/api/staff/search")
def search_staff_by_expertise():
    expertise_query = request.args.get("expertise", "")
    conn = get_db_connection()

    results = conn.execute(
        """SELECT DISTINCT staff.staff_id, staff.name, departments.department_name, staff.position, staff.status, staff_expertise.expertise_area, staff_expertise.skill_level 
        FROM staff
        JOIN staff_expertise ON staff.staff_id = staff_expertise.staff_id
        JOIN departments ON staff.department_id = departments.department_id
        WHERE staff_expertise.expertise_area LIKE ?""", (f"%{expertise_query}%",)
    ).fetchall()

    conn.close()
    return jsonify([dict(row) for row in results])

@app.route("/api/staff/filter")
def filter_staff():
    department_id = request.args.get("department_id")
    position = request.args.get("position")

    conn = get_db_connection()

    query = """SELECT staff.staff_id, staff.name, departments.department_name, staff.position, staff.employment_type, staff.status, staff_expertise.expertise_area
            FROM staff
            JOIN departments ON staff.department_id = departments.department_id
            LEFT JOIN staff_expertise ON staff.staff_id = staff_expertise.staff_id
            WHERE 1=1"""
    params = []

    if department_id:
        query += " AND staff.department_id = ?"
        params.append(department_id)

    if position:
        query += " AND staff.position = ?"
        params.append(position)

    results = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(row) for row in results])

@app.route("/api/departments")
def get_all_departments():
    conn = get_db_connection()
    departments = conn.execute(
        "SELECT department_id, department_name FROM departments"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in departments])

@app.route("/api/staff/<int:staff_id>/generate_analysis", methods=["POST"])
def generate_staff_analysis(staff_id):
    conn = get_db_connection()
 
    staff = conn.execute(
        """SELECT staff.name, staff.position, staff.employment_type, staff.status,
           departments.department_name
        FROM staff
        JOIN departments ON staff.department_id = departments.department_id
        WHERE staff.staff_id = ?""", (staff_id,)
    ).fetchone()
 
    if staff is None:
        conn.close()
        return jsonify({"error": "Staff member not found"}), 404
 
    # Aggregate ALL expertise and qualification rows, not just one (fixes
    # the earlier bug where fetchone() silently dropped extra rows)
    expertise_rows = conn.execute(
        """SELECT expertise_area, skill_level
        FROM staff_expertise
        WHERE staff_id = ?""", (staff_id,)
    ).fetchall()
 
    qualification_rows = conn.execute(
        """SELECT qualification_name, institution, year_obtained
        FROM staff_qualifications
        WHERE staff_id = ?""", (staff_id,)
    ).fetchall()
 
    if expertise_rows:
        expertise_list = "\n".join(
            f"- {row['expertise_area']} (skill level {row['skill_level']}/5)"
            for row in expertise_rows
        )
    else:
        expertise_list = "None supplied"
 
    if qualification_rows:
        qualifications_list = "\n".join(
            f"- {row['qualification_name']}, {row['institution']} ({row['year_obtained']})"
            for row in qualification_rows
        )
    else:
        qualifications_list = "None supplied"
 
    # Suitability score: still a simple rule-based figure derived from data,
    # not model output -- kept explicit rather than implying the LLM produced it
    if expertise_rows:
        avg_skill_level = sum(row["skill_level"] for row in expertise_rows) / len(expertise_rows)
        suitability_score = round(avg_skill_level * 2, 1)
    else:
        suitability_score = 0.0
 
    system_prompt = load_prompt("staff_analysis_system_prompt.txt")
    task_prompt = load_prompt("staff_analysis_task_prompt.txt")
 
    task_prompt = (
        task_prompt
        .replace("{{STAFF_NAME}}", staff["name"])
        .replace("{{POSITION}}", staff["position"])
        .replace("{{DEPARTMENT}}", staff["department_name"])
        .replace("{{EMPLOYMENT_TYPE}}", staff["employment_type"])
        .replace("{{STATUS}}", staff["status"])
        .replace("{{EXPERTISE_LIST}}", expertise_list)
        .replace("{{QUALIFICATIONS_LIST}}", qualifications_list)
    )
 
    try:
        summary = generate_response(task_prompt, system_prompt=system_prompt)
    except Exception as e:
        conn.close()
        return jsonify({"error": f"AI service unavailable: {e}"}), 503
 
    conn.execute(
        """INSERT INTO staff_ai_analysis (staff_id, generated_summary, suitability_score, date_generated)
        VALUES (?, ?, ?, ?)""",
        (staff_id, summary, suitability_score, date.today().isoformat())
    )
 
    conn.commit()
    conn.close()
    return jsonify({
        "message": "AI analysis successfully added",
        "generated_summary": summary,
        "suitability_score": suitability_score
    }), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

