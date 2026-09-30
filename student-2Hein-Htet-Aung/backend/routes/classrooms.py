from flask import Blueprint, jsonify, request
import requests

from services.allocation_rules import is_classroom_available
from services.database_api import (
    get_classrooms,
    get_classroom_by_id_response,
    create_classroom_response,
    update_classroom_response,
    delete_classroom_response,
    get_teaching_allocations,
)
from views.html_formatters import (
    format_classroom_html,
    format_classrooms_html,
)


classrooms_bp = Blueprint("classrooms", __name__)


@classrooms_bp.get("/classrooms/available")
def check_classroom_availability():
    classroom_id = request.args.get("classroom_id", "").strip().upper()
    date = request.args.get("date", "").strip()
    start_time = request.args.get("start_time", "").strip()
    end_time = request.args.get("end_time", "").strip()
    year = request.args.get("year", "").strip()

    if not year or not year.isdigit() or len(year) != 4:
        return jsonify(
            {"error": "A valid 4-digit year is required."}
        ), 400

    if not classroom_id:
        return jsonify({"error": "classroom_id is required."}), 400

    if not date:
        return jsonify({"error": "date is required."}), 400

    if not start_time:
        return jsonify({"error": "start_time is required."}), 400

    if not end_time:
        return jsonify({"error": "end_time is required."}), 400

    try:
        classroom_response = get_classroom_by_id_response(classroom_id)

        if classroom_response.status_code == 404:
            return jsonify({"error": "Classroom not found."}), 404

        classroom_response.raise_for_status()

        allocations = get_teaching_allocations()

        result = is_classroom_available(
            classroom_id,
            date,
            int(year),
            start_time,
            end_time,
            allocations,
        )

        return jsonify(result), 200

    except requests.RequestException as exc:
        return jsonify(
            {
                "error": "Failed to check classroom availability.",
                "details": str(exc),
            }
        ), 503


@classrooms_bp.get("/classrooms")
def get_classrooms_route():
    try:
        return format_classrooms_html(get_classrooms()), 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve classrooms from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@classrooms_bp.get("/classrooms/<string:classroom_id>")
def get_classroom_by_id(classroom_id):
    classroom_id = classroom_id.strip().upper()

    try:
        response = get_classroom_by_id_response(classroom_id)

        if response.status_code == 404:
            return "<p>Classroom not found.</p>", 404

        response.raise_for_status()

        return format_classroom_html(response.json()), 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve classroom from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@classrooms_bp.post("/classrooms")
def create_classroom():
    data = request.get_json(silent=True)

    if not data:
        return "<p>Classroom data is required.</p>", 400

    try:
        response = create_classroom_response(data)

        if response.status_code == 400:
            return (
                f"<p>{response.json().get('error', 'Unable to create classroom.')}</p>",
                400,
            )

        response.raise_for_status()

        return "<p>Classroom created.</p>", 201

    except requests.RequestException as exc:
        return (
            "<p>Failed to create classroom in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@classrooms_bp.put("/classrooms/<string:classroom_id>")
def update_classroom(classroom_id):
    data = request.get_json(silent=True)
    classroom_id = classroom_id.strip().upper()

    if not data:
        return "<p>Classroom data is required.</p>", 400

    try:
        response = update_classroom_response(classroom_id, data)

        if response.status_code == 404:
            return "<p>Classroom not found.</p>", 404

        if response.status_code == 400:
            return (
                f"<p>{response.json().get('error', 'Unable to update classroom.')}</p>",
                400,
            )

        response.raise_for_status()

        return "<p>Classroom updated.</p>", 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to update classroom in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@classrooms_bp.delete("/classrooms/<string:classroom_id>")
def delete_classroom(classroom_id):
    classroom_id = classroom_id.strip().upper()

    try:
        response = delete_classroom_response(classroom_id)

        if response.status_code == 404:
            return "<p>Classroom not found.</p>", 404

        if response.status_code == 400:
            return (
                f"<p>{response.json().get('error', 'Unable to delete classroom.')}</p>",
                400,
            )

        response.raise_for_status()

        return "<p>Classroom deleted.</p>", 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to delete classroom from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )