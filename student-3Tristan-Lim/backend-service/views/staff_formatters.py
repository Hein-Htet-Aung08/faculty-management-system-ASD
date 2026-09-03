from html import escape

from views.html_formatters import _table, message, stamp


def _esc(value):
    return escape("" if value is None else str(value))


def format_directory(directory):
    return _table(
        ["Staff", "Name", "Department", "Position", "Employment", "Status", "Expertise"],
        [
            (
                entry["staff_id"],
                entry["name"],
                entry["department_name"],
                entry["position"],
                entry["employment_type"],
                entry["status"],
                ", ".join(entry["expertise"]) or "-",
            )
            for entry in directory
        ],
    )


def format_expertise_results(rows, expertise):
    if not rows:
        return message(f"No staff found with expertise matching '{expertise}'.")

    table = _table(
        ["Staff", "Name", "Department", "Position", "Status", "Expertise", "Skill"],
        [
            (
                r.get("staff_id"),
                r.get("name"),
                r.get("department_name"),
                r.get("position"),
                r.get("status"),
                r.get("expertise_area"),
                r.get("skill_level"),
            )
            for r in rows
        ],
    )
    return f'<p class="project-id">Matching "{_esc(expertise)}"</p>{table}'


def format_staff_with_workload(record, workload):
    header = (
        f'<h3>{_esc(record.get("name"))} &mdash; staff {record.get("staff_id")}</h3>'
        f'<p class="project-id">{_esc(record.get("department_name"))} &middot; '
        f'{_esc(record.get("position"))} &middot; '
        f'{_esc(record.get("employment_type"))} &middot; '
        f'{_esc(record.get("status"))}</p>'
        f'<p class="project-id">{_esc(record.get("email"))} &middot; '
        f'{_esc(record.get("phone"))}</p>'
    )

    if workload is None:
        return header + message(
        )

    return (
        f"{header}"
        f'<h4>Workload {stamp(workload["status"])}</h4>'
        f'<p class="project-id">{workload["computed_hours"]:.1f}h of '
        f'{workload["cap"]:.1f}h cap &middot; headroom '
        f'{workload["headroom"]:+.1f}h &middot; '
        f'{len(workload["clashes"])} clash(es)</p>'
    )


def format_reconciliation(directory, analyses):
    staff_by_id = {entry["staff_id"]: entry for entry in directory}
    workload_by_id = {a["staff_id"]: a for a in analyses}

    rows = []
    for staff_id in sorted(set(staff_by_id) | set(workload_by_id)):
        staff = staff_by_id.get(staff_id)
        workload = workload_by_id.get(staff_id)

        if staff and workload:
            agree = staff["name"] == workload["staff_name"]
            state = "matched" if agree else "name mismatch"
        elif staff:
            state = "no workload profile"
        else:
            state = "no staff record"

        rows.append((
            staff_id,
            staff["name"] if staff else "-",
            workload["staff_name"] if workload else "-",
            state,
        ))

    matched = sum(1 for r in rows if r[3] == "matched")
    summary = message(
        f"{len(staff_by_id)} staff records, {len(workload_by_id)} workload profiles, "
        f"{matched} fully matched on staff_id.",
        "info" if matched == len(rows) else "warn",
    )

    return summary + _table(
        ["Staff ID", "Staff service name", "Workload profile name", "State"], rows
    )
