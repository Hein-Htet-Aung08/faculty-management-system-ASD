import requests
from flask import Blueprint, request

from services import database_api as db
from services import workload_rules as rules
from views import html_formatters as fmt

workload_bp = Blueprint("workload_ui", __name__)

# resource -> (table, form fields, numeric fields)
RESOURCES = {
    "entries": (
        "workload_entry",
        ["staff_id", "activity_type", "description", "hours_per_week",
         "start_date", "end_date", "semester", "source_service"],
        {"staff_id": int, "hours_per_week": float},
    ),
    "availability": (
        "availability_slot",
        ["staff_id", "day_of_week", "start_time", "end_time",
         "availability", "is_recurring"],
        {"staff_id": int, "is_recurring": int},
    ),
    "leave": (
        "leave_record",
        ["staff_id", "leave_type", "start_date", "end_date", "reason", "approval"],
        {"staff_id": int},
    ),
}

LIST_FORMATTERS = {
    "entries": fmt.format_entries,
    "availability": fmt.format_availability,
    "leave": fmt.format_leave,
}


def _payload_from_form(resource):
    _table, fields, numeric = RESOURCES[resource]
    payload = {}
    for field in fields:
        raw = request.form.get(field)
        if raw is None or raw == "":
            continue
        caster = numeric.get(field)
        try:
            payload[field] = caster(raw) if caster else raw
        except (TypeError, ValueError):
            return None, fmt.message(f"'{field}' must be numeric.", "warn")
    return payload, None


def _refresh(resource):
    """Return the current list fragment for a resource, honouring ?staff_id=."""
    table, _fields, _numeric = RESOURCES[resource]
    staff_id = request.values.get("staff_id", "")
    rows = db.list_rows(table, staff_id=staff_id)
    return LIST_FORMATTERS[resource](rows)


@workload_bp.get("/")
@workload_bp.get("/health")
def health():
    return "<p>backend-service (workload-and-availability) running</p>", 200


# ------------------------------------------------------------------ profiles ---

@workload_bp.get("/profiles")
def profiles():
    try:
        rows = db.list_rows(
            "staff_workload_profile",
            department=request.args.get("department"),
            status=request.args.get("status"),
            semester=request.args.get("semester"),
        )
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return fmt.format_profiles_table(rows), 200


@workload_bp.get("/profiles/by-staff")
def profile_by_staff():
    staff_id = request.args.get("staff_id", "").strip()
    if not staff_id:
        return fmt.message("staff_id is required.", "warn"), 400
    try:
        timetable = db.get_timetable(staff_id)
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return fmt.format_profile_detail(timetable), 200


@workload_bp.get("/overloads")
def overloads():
    """Profiles flagged overloaded (default) or any status via ?status=."""
    status = request.args.get("status", "overloaded")
    try:
        rows = db.list_rows("staff_workload_profile", status=status)
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return fmt.format_profiles_table(rows), 200


@workload_bp.get("/alerts")
def alerts():
    try:
        rows = db.list_rows(
            "workload_alert",
            status=request.args.get("status"),
            alert_type=request.args.get("alert_type"),
            staff_id=request.args.get("staff_id"),
        )
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return fmt.format_alerts(rows), 200


@workload_bp.get("/recommendations")
def recommendations():
    try:
        rows = db.list_rows(
            "rebalance_recommendation",
            decision_status=request.args.get("decision_status"),
            staff_id=request.args.get("staff_id"),
        )
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return fmt.format_recommendations(rows), 200


# ------------------------------------------------------------------ analysis ---

def _load_workload_dataset():
    """Fetch every table the rules engine needs, grouped by staff_id."""
    profiles = db.list_rows("staff_workload_profile")
    rule_rows = db.list_rows("workload_rule")

    grouped = {p["staff_id"]: {"profile": p, "entries": [], "slots": [], "leave": []}
               for p in profiles}

    for table, key in (("workload_entry", "entries"),
                       ("availability_slot", "slots"),
                       ("leave_record", "leave")):
        for row in db.list_rows(table):
            bucket = grouped.get(row["staff_id"])
            if bucket is not None:
                bucket[key].append(row)

    return grouped, rule_rows


def _analyse_all():
    grouped, rule_rows = _load_workload_dataset()
    return [
        rules.analyse_staff(b["profile"], b["entries"], b["slots"], b["leave"], rule_rows)
        for b in grouped.values()
    ]


@workload_bp.get("/analysis")
def analysis():
    """Recomputed load and clashes: one staff member via ?staff_id=, else all."""
    staff_id = request.args.get("staff_id", "").strip()
    try:
        results = _analyse_all()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    if staff_id:
        results = [r for r in results if str(r["staff_id"]) == staff_id]
        if not results:
            return fmt.message(f"No workload profile for staff_id {staff_id}.", "warn"), 404
        return fmt.format_analysis_detail(results[0]), 200

    return fmt.format_analysis_table(results), 200


@workload_bp.get("/clashes")
def clashes():
    staff_id = request.args.get("staff_id", "").strip()
    try:
        results = _analyse_all()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    found = []
    for result in results:
        if staff_id and str(result["staff_id"]) != staff_id:
            continue
        for clash in result["clashes"]:
            found.append({**clash, "staff_name": result["staff_name"]})

    return fmt.format_clashes(found), 200


@workload_bp.get("/calendar")
def calendar():
    """Weekly availability grid for one staff member."""
    staff_id = request.args.get("staff_id", "").strip()
    if not staff_id:
        return fmt.message("staff_id is required for the calendar view.", "warn"), 400

    try:
        slots = db.list_rows("availability_slot", staff_id=staff_id)
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    if not slots:
        return fmt.message(f"No availability recorded for staff {staff_id}.", "info"), 200

    grid = rules.build_calendar_grid(slots)
    return fmt.format_calendar(grid, rules.CALENDAR_DAYS), 200


@workload_bp.post("/alerts/recompute")
def recompute_alerts():
    """Write computed overload/underload/clash alerts back to the database.

    Existing open alerts of the same type for the same staff member are left
    alone, so running this repeatedly does not duplicate rows.
    """
    try:
        results = _analyse_all()
        existing = db.list_rows("workload_alert", status="open")
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    seen = {(a["staff_id"], a["alert_type"], a["message"]) for a in existing}

    created, failed = 0, 0
    for result in results:
        for alert in rules.build_alerts(result):
            if (alert["staff_id"], alert["alert_type"], alert["message"]) in seen:
                continue
            try:
                response = db.create_row("workload_alert", alert)
                if response.status_code >= 400:
                    failed += 1
                    continue
            except requests.RequestException:
                failed += 1
                continue
            seen.add((alert["staff_id"], alert["alert_type"], alert["message"]))
            created += 1

    drifted = [r for r in results if r["drift"]]
    return fmt.format_recompute_summary(created, failed, len(results), drifted), 200


# --------------------------------------------------------- generic CRUD views ---

@workload_bp.get("/<resource>")
def list_resource(resource):
    if resource not in RESOURCES:
        return fmt.message(f"unknown resource '{resource}'.", "warn"), 404
    table, _fields, _numeric = RESOURCES[resource]
    try:
        rows = db.list_rows(
            table,
            staff_id=request.args.get("staff_id"),
            approval=request.args.get("approval"),
        )
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
    return LIST_FORMATTERS[resource](rows), 200


@workload_bp.post("/<resource>")
def create_resource(resource):
    if resource not in RESOURCES:
        return fmt.message(f"unknown resource '{resource}'.", "warn"), 404
    table, _fields, _numeric = RESOURCES[resource]

    payload, error = _payload_from_form(resource)
    if error:
        return error, 400
    if not payload:
        return fmt.message("No fields supplied.", "warn"), 400

    try:
        response = db.create_row(table, payload)
        if response.status_code >= 400:
            return fmt.message(f"create failed: {response.text}", "error"), response.status_code
        return _refresh(resource), 201
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503


@workload_bp.route("/<resource>/<int:row_id>", methods=["PUT", "PATCH"])
def update_resource(resource, row_id):
    if resource not in RESOURCES:
        return fmt.message(f"unknown resource '{resource}'.", "warn"), 404
    table, _fields, _numeric = RESOURCES[resource]

    payload, error = _payload_from_form(resource)
    if error:
        return error, 400
    if not payload:
        return fmt.message("No fields supplied.", "warn"), 400

    try:
        response = db.update_row(table, row_id, payload)
        if response.status_code == 404:
            return fmt.message("Record not found.", "warn"), 404
        if response.status_code >= 400:
            return fmt.message(f"update failed: {response.text}", "error"), response.status_code
        return _refresh(resource), 200
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503


@workload_bp.delete("/<resource>/<int:row_id>")
def delete_resource(resource, row_id):
    if resource not in RESOURCES:
        return fmt.message(f"unknown resource '{resource}'.", "warn"), 404
    table, _fields, _numeric = RESOURCES[resource]

    try:
        response = db.delete_row(table, row_id)
        if response.status_code == 404:
            return fmt.message("Record not found.", "warn"), 404
        if response.status_code >= 400:
            return fmt.message(f"delete failed: {response.text}", "error"), response.status_code
        return _refresh(resource), 200
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503
