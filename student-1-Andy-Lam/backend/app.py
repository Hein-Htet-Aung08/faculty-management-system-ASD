from flask import Flask, jsonify, request
import sqlite3
from pathlib import Path

app = Flask(__name__)

DATA_DIR = Path(__file__).parent.parent/"database"/"staff.db"

def get_db_connection():
    conn = sqlite3.connect(DATA_DIR)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@app.route("/api/staff")
def get_all_staff():
    conn = get_db_connection()
    staff = conn.execute(
        """SELECT staff.staff_id, staff.name, departments.department_name, staff.position, staff.employment_type, staff.status
        FROM staff
        JOIN departments ON staff.department_id = departments.department_id"""
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in staff])

@app.route("/api/staff/<int:staff_id>")
def get_staff_by_id(staff_id):
    conn = get_db_connection()
    staff = conn.execute(
        """SELECT staff.staff_id, staff.name, staff.email, staff.phone, departments.department_name, staff.position, staff.employment_type, staff.status
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
        conn.commit()
        new_staff_id = cursor.lastrowid
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

