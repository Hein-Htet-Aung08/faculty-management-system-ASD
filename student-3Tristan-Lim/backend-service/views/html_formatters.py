from html import escape

STAMP_STATUS = {
    "ok": "status-active",
    "accepted": "status-active",
    "approved": "status-active",
    "underloaded": "status-applied",
    "pending": "status-applied",
    "overridden": "status-in-progress",
    "overloaded": "status-rejected",
    "rejected": "status-rejected",
}

# Availability states drawn with the shared palette rather than custom classes.
SLOT_COLOUR = {
    "available": "var(--ledger-green)",
    "preferred": "var(--gold-seal)",
    "unavailable": "var(--alert-rust)",
}


def _esc(value):
    return escape("" if value is None else str(value))


def stamp(status):
    """A status badge using the shared stamp element."""
    css = STAMP_STATUS.get(str(status).lower(), "status-proposed")
    return f'<span class="stamp {css}">{_esc(status)}</span>'


def message(text, kind="info"):
    css = "empty-state" if kind == "info" else "error-state"
    return f'<p class="{css}">{_esc(text)}</p>'


def _table(headers, rows):
    if not rows:
        return '<p class="empty-state">No records.</p>'
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{_esc(c)}</td>" for c in row)
        body += f"<tr>{cells}</tr>"
    return f'<table class="ledger-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


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
        f'<h3>{_esc(profile["staff_name"])} {stamp(profile["status"])}</h3>'
        f'<p class="project-id">{_esc(profile["department"])} &middot; '
        f'{_esc(profile["semester"])} &middot; '
        f'fraction {profile["contracted_fraction"]:.1f} &middot; '
        f'{profile["current_total_hours"]:.1f}h of {profile["max_weekly_hours"]:.1f}h</p>'
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


# ------------------------------------------------- computed workload analysis ---

def format_analysis_table(results):
    rows = [
        (
            r["staff_id"],
            r["staff_name"],
            r["department"],
            f'{r["computed_hours"]:.1f}',
            f'{r["cap"]:.1f}' if r["cap"] is not None else "-",
            f'{r["headroom"]:+.1f}' if r["headroom"] is not None else "-",
            len(r["clashes"]),
            r["status"],
        )
        for r in sorted(results, key=lambda r: r["staff_id"])
    ]
    return _table(
        ["Staff", "Name", "Dept", "Hours", "Cap", "Headroom", "Clashes", "Status"],
        rows,
    )


def format_analysis_detail(result):
    activity_rows = "".join(
        f"<li>{_esc(activity)}: {hours:.1f}h</li>"
        for activity, hours in sorted(result["by_activity"].items())
    )
    clash_rows = "".join(
        f'<li>{_esc(c["kind"])}: {_esc(c["detail"])}</li>' for c in result["clashes"]
    ) or '<li class="empty-state">None detected.</li>'

    drift_note = ""
    if result["drift"]:
        drift_note = message(
            f'Stored profile reads {result["recorded_hours"]:.1f}h but entries total '
            f'{result["computed_hours"]:.1f}h ({result["drift"]:+.1f}h drift).',
            "warn",
        )

    return f"""
<h3>{_esc(result["staff_name"])} &mdash; staff {result["staff_id"]}
    {stamp(result["status"])}</h3>
<p class="project-id">{_esc(result["department"])} &middot;
   {result["computed_hours"]:.1f}h of {result["cap"]:.1f}h cap
   (warning at {result["warning_threshold"]:.1f}h,
    underload below {result["underload_floor"]:.1f}h)</p>
{drift_note}
<h4>Hours by activity</h4>
<ul>{activity_rows}</ul>
<h4>Clashes</h4>
<ul>{clash_rows}</ul>
""".strip()


def format_clashes(clashes):
    return _table(
        ["Staff", "Name", "Kind", "Detail"],
        [(c["staff_id"], c.get("staff_name"), c["kind"], c["detail"]) for c in clashes],
    )


def format_recompute_summary(created, failed, evaluated, drifted):
    lines = [
        message(f"Evaluated {evaluated} staff profiles. Raised {created} new alert(s).")
    ]
    if failed:
        lines.append(message(f"{failed} alert(s) could not be written.", "error"))
    if drifted:
        detail = "".join(
            f'<li>{_esc(d["staff_name"])}: stored {d["recorded_hours"]:.1f}h vs '
            f'computed {d["computed_hours"]:.1f}h ({d["drift"]:+.1f}h)</li>'
            for d in drifted
        )
        lines.append(f"<h4>Profiles out of step with their entries</h4><ul>{detail}</ul>")
    return "".join(lines)


def format_calendar(grid, days, start_hour=8, end_hour=20):
    """Weekly availability grid, one row per hour.

    Cell shading uses the shared palette variables inline rather than custom
    classes, so the grid follows the team theme without adding to the stylesheet.
    """
    header = "".join(f"<th>{_esc(day)}</th>" for day in days)

    rows = ""
    for hour in range(start_hour, end_hour):
        cells = ""
        for day in days:
            availability = grid[day].get(hour)
            colour = SLOT_COLOUR.get(availability)
            attrs = (f' style="background:{colour}" title="{_esc(availability)}"'
                     if colour else "")
            cells += f"<td{attrs}></td>"
        rows += f'<tr><td class="project-id">{hour:02d}:00</td>{cells}</tr>'

    swatches = "".join(
        f'<span class="project-id" style="margin-right:1rem">'
        f'<span style="display:inline-block;width:.8rem;height:.8rem;'
        f'background:{colour};vertical-align:middle;margin-right:.3rem"></span>'
        f"{_esc(name)}</span>"
        for name, colour in SLOT_COLOUR.items()
    )

    return (
        f'<table class="ledger-table"><thead><tr><th></th>{header}</tr></thead>'
        f"<tbody>{rows}</tbody></table>"
        f'<p style="margin-top:.5rem">{swatches}</p>'
    )
