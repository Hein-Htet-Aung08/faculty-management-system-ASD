import os
import sqlite3

from flask import Flask, jsonify, request

from schema import TABLES, column_names

app = Flask(__name__)

DATABASE_NAME = os.getenv("DATABASE_PATH", "/app/data/workload.db")

# columns the list endpoints allow as ?key=value filters
FILTERABLE = {"staff_id", "department", "semester", "status", "approval",
              "decision_status", "alert_type", "activity_type", "day_of_week"}


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def _table_or_404(table):
    return table if table in TABLES else None


@app.get("/health")
@app.get("/")
def health():
    return jsonify({"service": "database-service",
                    "feature": "workload-and-availability",
                    "status": "running",
                    "tables": sorted(TABLES)})


@app.get("/<table>")
def list_rows(table):
    if _table_or_404(table) is None:
        return jsonify({"error": f"unknown table '{table}'"}), 404

    clauses, params = [], []
    for key in request.args:
        if key in FILTERABLE and key in TABLES[table]["columns"]:
            clauses.append(f"{key} = ?")
            params.append(request.args.get(key))

    sql = f"SELECT * FROM {table}"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    conn = get_db_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.get("/<table>/<int:row_id>")
def get_row(table, row_id):
    if _table_or_404(table) is None:
        return jsonify({"error": f"unknown table '{table}'"}), 404

    pk = TABLES[table]["pk"]
    conn = get_db_connection()
    row = conn.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (row_id,)).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(row))


@app.post("/<table>")
def create_row(table):
    if _table_or_404(table) is None:
        return jsonify({"error": f"unknown table '{table}'"}), 404

    payload = request.get_json(silent=True) or {}
    pk = TABLES[table]["pk"]
    writable = [c for c in column_names(table) if c != pk]

    provided = {c: payload[c] for c in writable if c in payload}
    if not provided:
        return jsonify({"error": f"no writable fields supplied; expected any of {writable}"}), 400

    cols = list(provided)
    placeholders = ", ".join("?" for _ in cols)
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
            [provided[c] for c in cols],
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (new_id,)).fetchone()
    except sqlite3.Error as exc:
        conn.close()
        return jsonify({"error": str(exc)}), 400
    conn.close()
    return jsonify(dict(row)), 201


@app.put("/<table>/<int:row_id>")
def update_row(table, row_id):
    if _table_or_404(table) is None:
        return jsonify({"error": f"unknown table '{table}'"}), 404

    payload = request.get_json(silent=True) or {}
    pk = TABLES[table]["pk"]
    writable = [c for c in column_names(table) if c != pk]
    provided = {c: payload[c] for c in writable if c in payload}
    if not provided:
        return jsonify({"error": "no writable fields supplied"}), 400

    conn = get_db_connection()
    exists = conn.execute(f"SELECT 1 FROM {table} WHERE {pk} = ?", (row_id,)).fetchone()
    if exists is None:
        conn.close()
        return jsonify({"error": "not found"}), 404

    assignments = ", ".join(f"{c} = ?" for c in provided)
    try:
        conn.execute(
            f"UPDATE {table} SET {assignments} WHERE {pk} = ?",
            [*provided.values(), row_id],
        )
        conn.commit()
        row = conn.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (row_id,)).fetchone()
    except sqlite3.Error as exc:
        conn.close()
        return jsonify({"error": str(exc)}), 400
    conn.close()
    return jsonify(dict(row))


@app.delete("/<table>/<int:row_id>")
def delete_row(table, row_id):
    if _table_or_404(table) is None:
        return jsonify({"error": f"unknown table '{table}'"}), 404

    pk = TABLES[table]["pk"]
    conn = get_db_connection()
    cursor = conn.execute(f"DELETE FROM {table} WHERE {pk} = ?", (row_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": row_id})


@app.get("/timetable")
def timetable():
    staff_id = request.args.get("staff_id", "").strip()
    if not staff_id:
        return jsonify({"error": "staff_id required"}), 400

    conn = get_db_connection()
    profile = conn.execute(
        "SELECT * FROM staff_workload_profile WHERE staff_id = ?", (staff_id,)
    ).fetchone()
    entries = conn.execute(
        "SELECT * FROM workload_entry WHERE staff_id = ? ORDER BY activity_type", (staff_id,)
    ).fetchall()
    slots = conn.execute(
        "SELECT * FROM availability_slot WHERE staff_id = ? ORDER BY day_of_week, start_time",
        (staff_id,),
    ).fetchall()
    leave = conn.execute(
        "SELECT * FROM leave_record WHERE staff_id = ? ORDER BY start_date", (staff_id,)
    ).fetchall()
    conn.close()

    return jsonify({
        "staff_id": int(staff_id),
        "profile": dict(profile) if profile else None,
        "workload_entries": [dict(r) for r in entries],
        "availability_slots": [dict(r) for r in slots],
        "leave_records": [dict(r) for r in leave],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5103, debug=True)
