"""Plain JSON endpoints for machine consumers (the shared ai-services/
mcp-server and ai-services/rag-server).

Every other route in this backend returns HTML fragments for the dashboard.
This blueprint exists only so the shared servers can read this feature's
data over HTTP, per the team convention that they go through each
student's backend/API rather than its database directly.
"""

import requests
from flask import Blueprint, jsonify, request

from services import database_api as db

api_bp = Blueprint("staff_workload_api", __name__, url_prefix="/api/staff-workload")


@api_bp.get("/profiles")
def profiles():
    try:
        rows = db.list_rows(
            "staff_workload_profile",
            status=request.args.get("status"),
            department=request.args.get("department"),
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"database-service unreachable: {exc}"}), 503
    return jsonify(rows), 200


@api_bp.get("/alerts")
def alerts():
    try:
        rows = db.list_rows(
            "workload_alert",
            status=request.args.get("status", "open"),
        )
    except requests.RequestException as exc:
        return jsonify({"error": f"database-service unreachable: {exc}"}), 503
    return jsonify(rows), 200
