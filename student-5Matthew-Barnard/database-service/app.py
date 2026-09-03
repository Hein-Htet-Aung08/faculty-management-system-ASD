import os
import sqlite3

from flask import Flask, jsonify, request

from database import get_connection, initialize_database, table_counts
from resource_config import RESOURCES, get_resource
from validation import validate_filter, validate_payload


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(test_config)

    initialize_database(seed=not app.config.get("SKIP_SEED", False))

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "performance-development-database",
            "tableCounts": table_counts(),
        })

    @app.get("/<resource>")
    def list_rows(resource):
        spec = get_resource(resource)
        if spec is None:
            return jsonify({"error": "resource not found"}), 404

        clauses = []
        params = []
        try:
            for field in spec["filters"]:
                value = request.args.get(field)
                if value not in (None, ""):
                    clauses.append(f"{field} = ?")
                    params.append(validate_filter(resource, field, value))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        query = f"SELECT * FROM {spec['table']}"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += f" ORDER BY {spec['order_by']}"

        connection = get_connection()
        try:
            rows = connection.execute(query, params).fetchall()
            return jsonify([dict(row) for row in rows])
        finally:
            connection.close()

    @app.get("/<resource>/<int:row_id>")
    def get_row(resource, row_id):
        spec = get_resource(resource)
        if spec is None:
            return jsonify({"error": "resource not found"}), 404

        connection = get_connection()
        try:
            row = connection.execute(
                f"SELECT * FROM {spec['table']} WHERE {spec['pk']} = ?", (row_id,)
            ).fetchone()
            if row is None:
                return jsonify({"error": f"{resource} record not found"}), 404
            return jsonify(dict(row))
        finally:
            connection.close()

    @app.post("/<resource>")
    def create_row(resource):
        spec = get_resource(resource)
        if spec is None:
            return jsonify({"error": "resource not found"}), 404
        try:
            values = validate_payload(resource, request.get_json(silent=True))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        columns = list(values)
        placeholders = ", ".join("?" for _ in columns)
        connection = get_connection()
        try:
            cursor = connection.execute(
                f"INSERT INTO {spec['table']} ({', '.join(columns)}) VALUES ({placeholders})",
                [values[column] for column in columns],
            )
            connection.commit()
            row = connection.execute(
                f"SELECT * FROM {spec['table']} WHERE {spec['pk']} = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return jsonify(dict(row)), 201
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            return jsonify({"error": f"record violates a database rule: {exc}"}), 400
        finally:
            connection.close()

    @app.put("/<resource>/<int:row_id>")
    def update_row(resource, row_id):
        spec = get_resource(resource)
        if spec is None:
            return jsonify({"error": "resource not found"}), 404
        try:
            changes = validate_payload(
                resource, request.get_json(silent=True), partial=True
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        connection = get_connection()
        try:
            exists = connection.execute(
                f"SELECT 1 FROM {spec['table']} WHERE {spec['pk']} = ?", (row_id,)
            ).fetchone()
            if exists is None:
                return jsonify({"error": f"{resource} record not found"}), 404

            assignments = ", ".join(f"{column} = ?" for column in changes)
            connection.execute(
                f"UPDATE {spec['table']} SET {assignments} WHERE {spec['pk']} = ?",
                [*changes.values(), row_id],
            )
            connection.commit()
            row = connection.execute(
                f"SELECT * FROM {spec['table']} WHERE {spec['pk']} = ?", (row_id,)
            ).fetchone()
            return jsonify(dict(row))
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            return jsonify({"error": f"record violates a database rule: {exc}"}), 400
        finally:
            connection.close()

    @app.delete("/<resource>/<int:row_id>")
    def delete_row(resource, row_id):
        spec = get_resource(resource)
        if spec is None:
            return jsonify({"error": "resource not found"}), 404

        connection = get_connection()
        try:
            cursor = connection.execute(
                f"DELETE FROM {spec['table']} WHERE {spec['pk']} = ?", (row_id,)
            )
            if cursor.rowcount == 0:
                return jsonify({"error": f"{resource} record not found"}), 404
            connection.commit()
            return "", 204
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            return jsonify({"error": f"record cannot be deleted: {exc}"}), 409
        finally:
            connection.close()

    @app.get("/meta/resources")
    def resources():
        return jsonify(sorted(RESOURCES))

    return app


app = create_app()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5105"))
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
