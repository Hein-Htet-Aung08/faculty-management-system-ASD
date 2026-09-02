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


# ------------------------------------------------- computed workload analysis ---

def _status_badge(status):
    return f'<span class="badge badge-{_esc(status)}">{_esc(status)}</span>'


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
    ) or "<li>None detected.</li>"

    drift_note = ""
    if result["drift"]:
        drift_note = (
            f'<p class="msg msg-warn">Stored profile reads '
            f'{result["recorded_hours"]:.1f}h but entries total '
            f'{result["computed_hours"]:.1f}h ({result["drift"]:+.1f}h drift).</p>'
        )

    return f"""
<section class="analysis">
  <h3>{_esc(result["staff_name"])} &mdash; staff {result["staff_id"]}
      {_status_badge(result["status"])}</h3>
  <p>{_esc(result["department"])} &middot;
     {result["computed_hours"]:.1f}h of {result["cap"]:.1f}h cap
     (warning at {result["warning_threshold"]:.1f}h,
      underload below {result["underload_floor"]:.1f}h)</p>
  {drift_note}
  <h4>Hours by activity</h4>
  <ul>{activity_rows}</ul>
  <h4>Clashes</h4>
  <ul>{clash_rows}</ul>
</section>
""".strip()


def format_clashes(clashes):
    return _table(
        ["Staff", "Name", "Kind", "Detail"],
        [(c["staff_id"], c.get("staff_name"), c["kind"], c["detail"]) for c in clashes],
    )


def format_recompute_summary(created, failed, evaluated, drifted):
    lines = [
        f'<p class="msg msg-info">Evaluated {evaluated} staff profiles. '
        f'Raised {created} new alert(s).</p>'
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
    """Weekly availability grid, one row per hour."""
    header = "".join(f"<th>{_esc(day)}</th>" for day in days)

    rows = ""
    for hour in range(start_hour, end_hour):
        cells = ""
        for day in days:
            availability = grid[day].get(hour)
            css = f' class="slot-{_esc(availability)}"' if availability else ""
            title = f' title="{_esc(availability)}"' if availability else ""
            cells += f"<td{css}{title}></td>"
        rows += f'<tr><td class="hour">{hour:02d}:00</td>{cells}</tr>'

    legend = (
        '<div class="calendar-legend">'
        '<span><i class="swatch slot-available"></i>available</span>'
        '<span><i class="swatch slot-preferred"></i>preferred</span>'
        '<span><i class="swatch slot-unavailable"></i>unavailable</span>'
        "</div>"
    )

    return (
        f'<table class="calendar"><thead><tr><th class="hour"></th>{header}</tr></thead>'
        f"<tbody>{rows}</tbody></table>{legend}"
    )
