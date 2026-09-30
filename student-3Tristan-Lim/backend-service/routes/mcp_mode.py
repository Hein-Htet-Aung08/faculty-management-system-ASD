import json
import os

from flask import Blueprint, jsonify, request

from services import database_api as db
from services import prompt_loader

mcp_bp = Blueprint("mcp_mode", __name__, url_prefix="/mcp")

VALID_STATUSES = {"overloaded", "underloaded", "ok"}
AVAILABLE_TOOLS = ["staff_count", "staff_by_status", "project_files", "ci_report"]


def _mcp_enabled():
    return os.getenv("MCP_ENABLED", "true").strip().lower() in ("1", "true", "on", "yes")


def _mode_active():
    return _mcp_enabled() and request.headers.get("X-MCP-Mode", "").strip().lower() == "on"


def _disabled_response():
    if not _mcp_enabled():
        return jsonify({"error": "MCP is disabled on this server (MCP_ENABLED=false)."}), 503
    return jsonify({"error": "MCP Mode is off. Send 'X-MCP-Mode: on' to use these tools."}), 400


def _arg(name, default=""):
    if request.is_json:
        value = (request.get_json(silent=True) or {}).get(name)
        if value is not None:
            return str(value)
    return request.values.get(name, default)


def _resolve_within_app_dir(relative_path):
    """Keep project_files/ci_report from reading outside student-3Tristan-Lim/."""
    candidate = (prompt_loader.APP_DIR / relative_path).resolve()
    app_dir = prompt_loader.APP_DIR.resolve()
    if candidate != app_dir and app_dir not in candidate.parents:
        return None
    return candidate


@mcp_bp.get("/health")
def health():
    return jsonify({
        "mcp_enabled": _mcp_enabled(),
        "mcp_mode_active": _mode_active(),
        "tools": AVAILABLE_TOOLS,
    }), 200


@mcp_bp.post("/tools/staff_count")
def staff_count():
    if not _mode_active():
        return _disabled_response()

    rows = db.list_rows("staff_workload_profile")
    return jsonify({"staff_count": len(rows)}), 200


@mcp_bp.post("/tools/staff_by_status")
def staff_by_status():
    if not _mode_active():
        return _disabled_response()

    status = _arg("status").strip().lower()
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    rows = db.list_rows("staff_workload_profile", status=status)
    return jsonify([
        {
            "staff_id": r["staff_id"],
            "staff_name": r["staff_name"],
            "department": r["department"],
            "current_total_hours": r["current_total_hours"],
            "max_weekly_hours": r["max_weekly_hours"],
            "status": r["status"],
        }
        for r in rows
    ]), 200


@mcp_bp.post("/tools/project_files")
def project_files():
    if not _mode_active():
        return _disabled_response()

    path = _resolve_within_app_dir(_arg("directory_path", "."))
    if path is None or not path.exists() or not path.is_dir():
        return jsonify({"error": f"Directory not found: {_arg('directory_path', '.')}"}), 404

    return jsonify(sorted(item.name for item in path.iterdir())), 200


@mcp_bp.post("/tools/ci_report")
def ci_report():
    if not _mode_active():
        return _disabled_response()

    report_path = _arg("report_path", "reports/report.json")
    report_file = _resolve_within_app_dir(report_path)

    if report_file is None or not report_file.exists():
        return jsonify({
            "error": "Report not found",
            "path": report_path,
            "hint": "Run the student-3-TristanLim.yml workflow to generate report.json",
        }), 404

    with report_file.open("r", encoding="utf-8") as file:
        return jsonify(json.load(file)), 200
