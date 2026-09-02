from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DATABASE_NAME = "/app/data/allocation.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@app.get("/")
def health():
    return jsonify({"service": "database-service", "status": "running"})

@app.get("/subjects")
def get_subjects():
    conn = get_db_connection()
    subjects = conn.execute(
        "SELECT subject_code, name, required_expertise FROM subjects"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in subjects])

@app.get("/subjects/<string:subject_code>")
def get_subject(subject_code):
    conn = get_db_connection()
    subject = conn.execute(
        "SELECT subject_code, name, required_expertise FROM subjects WHERE subject_code = ?",
        (subject_code,),
    ).fetchone()
    conn.close()

    if subject is None:
        return jsonify({"error": "Subject not found"}), 404

    return jsonify(dict(subject))

@app.get("/subject-offers")
def get_subject_offers():
    conn = get_db_connection()
    offers = conn.execute(
        "SELECT offer_id, subject_code, semester, year, expected_enrollment FROM subject_offers"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in offers])

@app.get("/subject-offers/<string:offer_id>")
def get_subject_offer(offer_id):
    conn = get_db_connection()
    offer = conn.execute(
        "SELECT offer_id, subject_code, semester, year, expected_enrollment FROM subject_offers WHERE offer_id = ?",
        (offer_id,),
    ).fetchone()
    conn.close()

    if offer is None:
        return jsonify({"error": "Subject offer not found"}), 404

    return jsonify(dict(offer))

@app.get("/classrooms")
def get_classrooms():
    conn = get_db_connection()
    classrooms = conn.execute(
        "SELECT classroom_id, building, floor, room_number, capacity, room_type, facilities FROM classrooms"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in classrooms])

@app.get("/classrooms/<string:classroom_id>")
def get_classroom(classroom_id):
    conn = get_db_connection()
    classroom = conn.execute(
        "SELECT classroom_id, building, floor, room_number, capacity, room_type, facilities FROM classrooms WHERE classroom_id = ?",
        (classroom_id,),
    ).fetchone()
    conn.close()

    if classroom is None:
        return jsonify({"error": "Classroom not found"}), 404

    return jsonify(dict(classroom))

@app.get("/teaching-allocations")
def get_teaching_allocations():
    conn = get_db_connection()
    allocations = conn.execute(
        """
        SELECT allocation_id, offer_id, assigned_staff_member,
               classroom_id, day, date_range, start_time,
               end_time, class_type, expected_class_size,
               allocation_status
        FROM teaching_allocations
        """
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in allocations])

@app.get("/teaching-allocations/<int:allocation_id>")
def get_teaching_allocation(allocation_id):
    conn = get_db_connection()
    allocation = conn.execute(
        """
        SELECT allocation_id, offer_id, assigned_staff_member,
               classroom_id, day, date_range, start_time,
               end_time, class_type, expected_class_size,
               allocation_status
        FROM teaching_allocations
        WHERE allocation_id = ?
        """,
        (allocation_id,),
    ).fetchone()
    conn.close()

    if allocation is None:
        return jsonify({"error": "Teaching allocation not found"}), 404

    return jsonify(dict(allocation))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6002, debug=True)