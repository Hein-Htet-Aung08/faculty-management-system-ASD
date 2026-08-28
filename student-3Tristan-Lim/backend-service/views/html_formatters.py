"""Render database rows as small HTML fragments for the HTMX frontend."""

from html import escape


def _esc(value):
    return escape("" if value is None else str(value))


def message(text, kind="info"):
    return f'<p class="msg msg-{kind}">{_esc(text)}</p>'


def _table(headers, rows):
    if not rows:
        return '<p class="msg msg-info">No records.</p>'
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{_esc(c)}</td>" for c in row)
        body += f"<tr>{cells}</tr>"
    return f'<table class="data-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def format_profiles_table(profiles):
    rows = [
        (
            p["staff_id"],
            p["staff_name"],
            p["department"],
            p["semester"],
            f'{p["contracted_fraction"]:.1f}',
            f'{p["current_total_hours"]:.1f} / {p["max_weekly_hours"]:.1f}',
            p["status"],
        )
        for p in profiles
    ]
    return _table(
        ["Staff", "Name", "Dept", "Semester", "Fraction", "Hours (cur/cap)", "Status"],
        rows,
    )


def format_profile_detail(timetable):
    profile = timetable.get("profile")
    if not profile:
        return message("No workload profile for that staff member.", "warn")

    header = (
        f'<div class="panel">'
        f'<h3>{_esc(profile["staff_name"])} '
        f'<span class="tag tag-{_esc(profile["status"])}">{_esc(profile["status"])}</span></h3>'
        f'<p>{_esc(profile["department"])} &middot; {_esc(profile["semester"])} &middot; '
        f'fraction {profile["contracted_fraction"]:.1f} &middot; '
        f'{profile["current_total_hours"]:.1f}h of {profile["max_weekly_hours"]:.1f}h</p>'
        f"</div>"
    )

    entries = _table(
        ["Activity", "Description", "Hrs/wk", "Start", "End", "Source"],
        [
            (
                e["activity_type"],
                e["description"],
                f'{e["hours_per_week"]:.1f}',
                e["start_date"],
                e["end_date"],
                e["source_service"],
            )
            for e in timetable.get("workload_entries", [])
        ],
    )

    slots = _table(
        ["Day", "Start", "End", "Availability", "Recurring"],
        [
            (
                s["day_of_week"],
                s["start_time"],
                s["end_time"],
                s["availability"],
                "yes" if s["is_recurring"] else "no",
            )
            for s in timetable.get("availability_slots", [])
        ],
    )

    leave = _table(
        ["Type", "Start", "End", "Approval"],
        [
            (l["leave_type"], l["start_date"], l["end_date"], l["approval"])
            for l in timetable.get("leave_records", [])
        ],
    )

    return (
        f"{header}"
        f"<h4>Workload entries</h4>{entries}"
        f"<h4>Availability</h4>{slots}"
        f"<h4>Leave</h4>{leave}"
    )


def format_entries(entries):
    return _table(
        ["ID", "Staff", "Activity", "Description", "Hrs/wk", "Start", "End", "Semester"],
        [
            (
                e["entry_id"],
                e["staff_id"],
                e["activity_type"],
                e["description"],
                f'{e["hours_per_week"]:.1f}',
                e["start_date"],
                e["end_date"],
                e["semester"],
            )
            for e in entries
        ],
    )


def format_availability(slots):
    return _table(
        ["ID", "Staff", "Day", "Start", "End", "Availability", "Recurring"],
        [
            (
                s["slot_id"],
                s["staff_id"],
                s["day_of_week"],
                s["start_time"],
                s["end_time"],
                s["availability"],
                "yes" if s["is_recurring"] else "no",
            )
            for s in slots
        ],
    )


def format_leave(records):
    return _table(
        ["ID", "Staff", "Type", "Start", "End", "Reason", "Approval"],
        [
            (
                r["leave_id"],
                r["staff_id"],
                r["leave_type"],
                r["start_date"],
                r["end_date"],
                r["reason"],
                r["approval"],
            )
            for r in records
        ],
    )


def format_alerts(alerts):
    return _table(
        ["ID", "Staff", "Type", "Severity", "Message", "Status", "Raised"],
        [
            (
                a["alert_id"],
                a["staff_id"],
                a["alert_type"],
                a["severity"],
                a["message"],
                a["status"],
                a["date_raised"],
            )
            for a in alerts
        ],
    )


def format_recommendations(recs):
    return _table(
        ["ID", "Alert", "Staff", "Suggested action", "To staff", "Rationale", "Decision"],
        [
            (
                r["rec_id"],
                r["alert_id"],
                r["staff_id"],
                r["suggested_action"],
                r["target_staff_id"],
                r["rationale"],
                r["decision_status"],
            )
            for r in recs
        ],
    )
