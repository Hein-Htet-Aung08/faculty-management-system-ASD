import requests
from flask import Blueprint, jsonify, request

from routes.workload_ui import _analyse_all
from services import staff_api
from views import html_formatters as fmt
from views import staff_formatters as fmt_staff

staff_bp = Blueprint("staff_directory", __name__, url_prefix="/staff")


@staff_bp.get("/health")
def health():
    try:
        directory = staff_api.staff_directory()
    except staff_api.StaffServiceUnavailable as exc:
        return fmt.message(
            f"Staff service unreachable at {staff_api.STAFF_SERVICE_URL}: {exc}",
            "error",
        ), 503

    return fmt.message(
        f"Staff service reachable at {staff_api.STAFF_SERVICE_URL} "
        f"- {len(directory)} staff records.",
    ), 200


@staff_bp.get("/expertise-areas")
def expertise_areas():
    """Distinct expertise areas across the staff roster, for the filter dropdown."""
    try:
        directory = staff_api.staff_directory()
    except staff_api.StaffServiceUnavailable as exc:
        return jsonify({"error": str(exc)}), 503

    areas = sorted({
        area
        for entry in directory
        for area in entry.get("expertise", [])
        if area
    })
    return jsonify(areas), 200


@staff_bp.get("/directory")
def directory():
    expertise = request.args.get("expertise", "").strip()

    try:
        if expertise:
            rows = staff_api.search_by_expertise(expertise)
            return fmt_staff.format_expertise_results(rows, expertise), 200
        return fmt_staff.format_directory(staff_api.staff_directory()), 200
    except staff_api.StaffServiceUnavailable as exc:
        return fmt.message(f"Staff service unavailable: {exc}", "error"), 503


@staff_bp.get("/<int:staff_id>")
def staff_detail(staff_id):
    try:
        record = staff_api.get_staff(staff_id)
    except staff_api.StaffServiceUnavailable as exc:
        return fmt.message(f"Staff service unavailable: {exc}", "error"), 503

    if record is None:
        return fmt.message(f"Staff {staff_id} not found in the staff service.", "warn"), 404

    try:
        analyses = _analyse_all()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    workload = next((a for a in analyses if a["staff_id"] == staff_id), None)
    return fmt_staff.format_staff_with_workload(record, workload), 200


@staff_bp.get("/reconcile")
def reconcile():
    try:
        directory = staff_api.staff_directory()
    except staff_api.StaffServiceUnavailable as exc:
        return fmt.message(f"Staff service unavailable: {exc}", "error"), 503

    try:
        analyses = _analyse_all()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    return fmt_staff.format_reconciliation(directory, analyses), 200
