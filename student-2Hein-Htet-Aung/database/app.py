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


@app.post("/subjects")
def create_subject():
    data = request.get_json()

    conn = get_db_connection()

    try:
        conn.execute(
            """
            INSERT INTO subjects (
                subject_code,
                name,
                required_expertise
            )
            VALUES (?, ?, ?)
            """,
            (
                data["subject_code"],
                data["name"],
                data["required_expertise"],
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject created"}), 201


@app.put("/subjects/<string:subject_code>")
def update_subject(subject_code):
    data = request.get_json()

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE subjects
            SET subject_code = ?,
                name = ?,
                required_expertise = ?
            WHERE subject_code = ?
            """,
            (
                data["subject_code"],
                data["name"],
                data["required_expertise"],
                subject_code,
            ),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Subject not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject updated"})


@app.delete("/subjects/<string:subject_code>")
def delete_subject(subject_code):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM subjects WHERE subject_code = ?",
            (subject_code,),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Subject not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject deleted"})


@app.post("/subject-offers")
def create_subject_offer():
    data = request.get_json()

    conn = get_db_connection()

    try:
        conn.execute(
            """
            INSERT INTO subject_offers (
                offer_id,
                subject_code,
                semester,
                year,
                expected_enrollment
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["offer_id"],
                data["subject_code"],
                data["semester"],
                data["year"],
                data["expected_enrollment"],
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject offer created"}), 201


@app.put("/subject-offers/<string:offer_id>")
def update_subject_offer(offer_id):
    data = request.get_json()

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE subject_offers
            SET offer_id = ?,
                subject_code = ?,
                semester = ?,
                year = ?,
                expected_enrollment = ?
            WHERE offer_id = ?
            """,
            (
                data["offer_id"],
                data["subject_code"],
                data["semester"],
                data["year"],
                data["expected_enrollment"],
                offer_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Subject offer not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject offer updated"})


@app.delete("/subject-offers/<string:offer_id>")
def delete_subject_offer(offer_id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM subject_offers WHERE offer_id = ?",
            (offer_id,),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Subject offer not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Subject offer deleted"})


@app.post("/classrooms")
def create_classroom():
    data = request.get_json()

    conn = get_db_connection()

    try:
        conn.execute(
            """
            INSERT INTO classrooms (
                classroom_id,
                building,
                floor,
                room_number,
                capacity,
                room_type,
                facilities
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["classroom_id"],
                data["building"],
                data["floor"],
                data["room_number"],
                data["capacity"],
                data["room_type"],
                data["facilities"],
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Classroom created"}), 201


@app.put("/classrooms/<string:classroom_id>")
def update_classroom(classroom_id):
    data = request.get_json()

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE classrooms
            SET classroom_id = ?,
                building = ?,
                floor = ?,
                room_number = ?,
                capacity = ?,
                room_type = ?,
                facilities = ?
            WHERE classroom_id = ?
            """,
            (
                data["classroom_id"],
                data["building"],
                data["floor"],
                data["room_number"],
                data["capacity"],
                data["room_type"],
                data["facilities"],
                classroom_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Classroom not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Classroom updated"})


@app.delete("/classrooms/<string:classroom_id>")
def delete_classroom(classroom_id):
    conn = get_db_connection()

    try:
        cursor = conn.execute(
            "DELETE FROM classrooms WHERE classroom_id = ?",
            (classroom_id,),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Classroom not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Classroom deleted"})


@app.post("/teaching-allocations")
def create_teaching_allocation():
    data = request.get_json()

    assigned_staff_member = data.get("assigned_staff_member")
    allocation_status = data["allocation_status"]

    if allocation_status == "NEEDS_ASSIGNMENT":
        assigned_staff_member = None

    if assigned_staff_member is None:
        allocation_status = "NEEDS_ASSIGNMENT"

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO teaching_allocations (
                offer_id,
                assigned_staff_member,
                classroom_id,
                day,
                date_range,
                start_time,
                end_time,
                class_type,
                expected_class_size,
                allocation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["offer_id"],
                assigned_staff_member,
                data["classroom_id"],
                data["day"],
                data["date_range"],
                data["start_time"],
                data["end_time"],
                data["class_type"],
                data["expected_class_size"],
                allocation_status,
            ),
        )

        allocation_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify(
        {
            "message": "Teaching allocation created",
            "allocation_id": allocation_id,
        }
    ), 201


@app.put("/teaching-allocations/<int:allocation_id>")
def update_teaching_allocation(allocation_id):
    data = request.get_json()

    assigned_staff_member = data.get("assigned_staff_member")
    allocation_status = data["allocation_status"]

    if allocation_status == "NEEDS_ASSIGNMENT":
        assigned_staff_member = None

    if assigned_staff_member is None:
        allocation_status = "NEEDS_ASSIGNMENT"

    conn = get_db_connection()

    try:
        cursor = conn.execute(
            """
            UPDATE teaching_allocations
            SET offer_id = ?,
                assigned_staff_member = ?,
                classroom_id = ?,
                day = ?,
                date_range = ?,
                start_time = ?,
                end_time = ?,
                class_type = ?,
                expected_class_size = ?,
                allocation_status = ?
            WHERE allocation_id = ?
            """,
            (
                data["offer_id"],
                assigned_staff_member,
                data["classroom_id"],
                data["day"],
                data["date_range"],
                data["start_time"],
                data["end_time"],
                data["class_type"],
                data["expected_class_size"],
                allocation_status,
                allocation_id,
            ),
        )

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"error": "Teaching allocation not found"}), 404

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

    conn.close()

    return jsonify({"message": "Teaching allocation updated"})


@app.delete("/teaching-allocations/<int:allocation_id>")
def delete_teaching_allocation(allocation_id):
    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM teaching_allocations WHERE allocation_id = ?",
        (allocation_id,),
    )

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Teaching allocation not found"}), 404

    conn.commit()
    conn.close()

    return jsonify({"message": "Teaching allocation deleted"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6002, debug=True)