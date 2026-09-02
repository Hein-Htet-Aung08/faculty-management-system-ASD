from datetime import date

import requests
from flask import Blueprint, Response, request

from routes.workload_ui import _analyse_all
from services import database_api as db
from views import csv_formatters as csv_fmt
from views import html_formatters as fmt

exports_bp = Blueprint("exports", __name__)

# Datasets that come straight from a database table.
TABLE_EXPORTS = {
    "profiles": "staff_workload_profile",
    "entries": "workload_entry",
    "availability": "availability_slot",
    "leave": "leave_record",
    "rules": "workload_rule",
    "alerts": "workload_alert",
    "recommendations": "rebalance_recommendation",
}

# Datasets computed by the rules engine.
COMPUTED_EXPORTS = ("analysis", "clashes")

FILTERS = ("staff_id", "department", "status", "approval", "alert_type",
           "decision_status", "activity_type", "semester")


def _csv_response(body, dataset):
    filename = f"workload-{dataset}-{date.today().isoformat()}.csv"
    return Response(
        body,
        # Flask appends the charset itself; setting it here would duplicate it.
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@exports_bp.get("/export/<dataset>.csv")
def export_csv(dataset):
    staff_id = request.args.get("staff_id", "").strip()

    if dataset in COMPUTED_EXPORTS:
        try:
            results = _analyse_all()
        except requests.RequestException as exc:
            return fmt.message(f"database-service unreachable: {exc}", "error"), 503

        if staff_id:
            results = [r for r in results if str(r["staff_id"]) == staff_id]
        department = request.args.get("department", "").strip()
        if department:
            results = [r for r in results if r["department"] == department]
        status = request.args.get("status", "").strip()
        if status and dataset == "analysis":
            results = [r for r in results if r["status"] == status]

        body = (csv_fmt.analysis_to_csv(results) if dataset == "analysis"
                else csv_fmt.clashes_to_csv(results))
        return _csv_response(body, dataset)

    table = TABLE_EXPORTS.get(dataset)
    if table is None:
        known = ", ".join(sorted([*TABLE_EXPORTS, *COMPUTED_EXPORTS]))
        return fmt.message(f"Unknown export '{dataset}'. Available: {known}.", "warn"), 404

    filters = {key: request.args.get(key) for key in FILTERS if request.args.get(key)}
    try:
        records = db.list_rows(table, **filters)
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    return _csv_response(csv_fmt.records_to_csv(records), dataset)


@exports_bp.get("/export")
def list_exports():
    """The datasets available for download, as an HTML fragment."""
    items = "".join(
        f'<li><code>{name}</code></li>'
        for name in sorted([*TABLE_EXPORTS, *COMPUTED_EXPORTS])
    )
    return f"<p>Available exports:</p><ul>{items}</ul>", 200
