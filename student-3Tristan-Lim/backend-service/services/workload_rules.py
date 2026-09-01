"""Workload evaluation: consolidate hours, apply caps, detect clashes.

The database seeds a `status` and a set of `workload_alert` rows, but those are
static. This module recomputes them from the underlying `workload_entry`,
`availability_slot` and `leave_record` data so the dashboard (and the AI agent)
reason over live figures rather than whatever was seeded.
"""

from datetime import date

# A staff member below this fraction of their cap is treated as underloaded.
UNDERLOAD_RATIO = 0.8

# Alert types this module owns. Recompute only touches these.
COMPUTED_TYPES = ("overload", "underload", "clash")

TEACHING_ACTIVITIES = ("teaching",)


# ------------------------------------------------------------------- helpers ---

def _minutes(hhmm):
    """'09:30' -> 570. Returns None when the value is not parseable."""
    try:
        hours, minutes = str(hhmm).split(":")
        return int(hours) * 60 + int(minutes)
    except (ValueError, AttributeError):
        return None


def ranges_overlap(start_a, end_a, start_b, end_b):
    """True when two [start, end) ranges share any point. Works for HH:MM or ISO dates."""
    if None in (start_a, end_a, start_b, end_b):
        return False
    return start_a < end_b and start_b < end_a


def times_overlap(slot_a, slot_b):
    return ranges_overlap(
        _minutes(slot_a["start_time"]), _minutes(slot_a["end_time"]),
        _minutes(slot_b["start_time"]), _minutes(slot_b["end_time"]),
    )


def dates_overlap(start_a, end_a, start_b, end_b):
    # ISO dates sort lexicographically, so plain string comparison is correct here.
    return ranges_overlap(start_a, end_a, start_b, end_b)


# --------------------------------------------------------------------- rules ---

def resolve_caps(profile, rules):
    """Return (cap, warning_threshold, underload_floor) in hours for one profile.

    The department rule applies where one exists, otherwise the university
    standard ('all'). Both are scaled by the contracted fraction, then bounded by
    the max_weekly_hours recorded on the profile itself.
    """
    department = profile.get("department")
    fraction = float(profile.get("contracted_fraction") or 1.0)
    profile_cap = float(profile.get("max_weekly_hours") or 0) or None

    rule = next((r for r in rules if r.get("applies_to") == department), None)
    if rule is None:
        rule = next((r for r in rules if r.get("applies_to") == "all"), None)
    if rule is None:
        return profile_cap, None, None

    cap = float(rule["max_total_hours"]) * fraction
    warn = float(rule["warning_threshold"]) * fraction

    if profile_cap is not None:
        cap = min(cap, profile_cap)
        warn = min(warn, profile_cap)

    return round(cap, 2), round(warn, 2), round(cap * UNDERLOAD_RATIO, 2)


def consolidate_hours(entries):
    """Sum hours_per_week across every contributing activity."""
    return round(sum(float(e.get("hours_per_week") or 0) for e in entries), 2)


def hours_by_activity(entries):
    totals = {}
    for entry in entries:
        activity = entry.get("activity_type") or "unknown"
        totals[activity] = round(totals.get(activity, 0) + float(entry.get("hours_per_week") or 0), 2)
    return totals


def evaluate_load(profile, entries, rules):
    """Classify one staff member's total load as overloaded / ok / underloaded."""
    total = consolidate_hours(entries)
    cap, warn, floor = resolve_caps(profile, rules)
    recorded = float(profile.get("current_total_hours") or 0)

    if cap is None:
        status, headroom = "ok", None
    elif total > cap:
        status, headroom = "overloaded", round(cap - total, 2)
    elif floor is not None and total < floor:
        status, headroom = "underloaded", round(cap - total, 2)
    else:
        status, headroom = "ok", round(cap - total, 2)

    return {
        "staff_id": profile["staff_id"],
        "staff_name": profile.get("staff_name"),
        "department": profile.get("department"),
        "computed_hours": total,
        "recorded_hours": recorded,
        # Non-zero drift means the stored profile is stale against its entries.
        "drift": round(total - recorded, 2),
        "cap": cap,
        "warning_threshold": warn,
        "underload_floor": floor,
        "headroom": headroom,
        "status": status,
        "by_activity": hours_by_activity(entries),
    }


# -------------------------------------------------------------------- clashes ---

def detect_availability_clashes(slots):
    """Two slots on the same day whose times overlap."""
    clashes = []
    for index, slot in enumerate(slots):
        for other in slots[index + 1:]:
            if slot.get("day_of_week") != other.get("day_of_week"):
                continue
            if not times_overlap(slot, other):
                continue
            clashes.append({
                "kind": "availability",
                "staff_id": slot["staff_id"],
                "detail": (
                    f"{slot['day_of_week']} {slot['start_time']}-{slot['end_time']} "
                    f"({slot['availability']}) overlaps "
                    f"{other['start_time']}-{other['end_time']} ({other['availability']})"
                ),
            })
    return clashes


def detect_leave_clashes(leave_records, entries):
    """Approved or pending leave that falls inside a teaching commitment."""
    clashes = []
    teaching = [e for e in entries if e.get("activity_type") in TEACHING_ACTIVITIES]

    for record in leave_records:
        if record.get("approval") == "rejected":
            continue
        for entry in teaching:
            if not dates_overlap(
                record["start_date"], record["end_date"],
                entry["start_date"], entry["end_date"],
            ):
                continue
            clashes.append({
                "kind": "leave",
                "staff_id": record["staff_id"],
                "detail": (
                    f"{record['leave_type']} leave {record['start_date']}..{record['end_date']} "
                    f"({record['approval']}) overlaps '{entry.get('description')}'"
                ),
            })
    return clashes


# ------------------------------------------------------------------ analysis ---

def analyse_staff(profile, entries, slots, leave_records, rules):
    """Full picture for one staff member: load classification plus clashes."""
    analysis = evaluate_load(profile, entries, rules)
    analysis["clashes"] = (
        detect_availability_clashes(slots) + detect_leave_clashes(leave_records, entries)
    )
    return analysis


def _severity_for_overload(total, cap):
    excess = total - cap
    if excess > cap * 0.05:
        return "high"
    if excess > 0:
        return "medium"
    return "low"


def build_alerts(analysis):
    """Turn one analysis result into alert rows ready for the database service."""
    raised = date.today().isoformat()
    alerts = []
    staff_id = analysis["staff_id"]
    total, cap = analysis["computed_hours"], analysis["cap"]

    if analysis["status"] == "overloaded":
        alerts.append({
            "staff_id": staff_id,
            "alert_type": "overload",
            "severity": _severity_for_overload(total, cap),
            "message": f"Total {total}h exceeds cap {cap}h for {analysis['department']}",
            "status": "open",
            "date_raised": raised,
        })
    elif analysis["status"] == "underloaded":
        alerts.append({
            "staff_id": staff_id,
            "alert_type": "underload",
            "severity": "low" if total >= analysis["underload_floor"] * 0.75 else "medium",
            "message": f"Total {total}h below underload floor {analysis['underload_floor']}h",
            "status": "open",
            "date_raised": raised,
        })
    elif cap is not None and total >= cap:
        alerts.append({
            "staff_id": staff_id,
            "alert_type": "overload",
            "severity": "low",
            "message": f"Total {total}h is at cap {cap}h - no headroom",
            "status": "open",
            "date_raised": raised,
        })

    for clash in analysis["clashes"]:
        alerts.append({
            "staff_id": staff_id,
            "alert_type": "clash",
            "severity": "medium" if clash["kind"] == "availability" else "low",
            "message": clash["detail"],
            "status": "open",
            "date_raised": raised,
        })

    return alerts


# ------------------------------------------------------------------ calendar ---

CALENDAR_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# When two slots cover the same hour, the more restrictive one is shown.
AVAILABILITY_PRECEDENCE = {"available": 0, "preferred": 1, "unavailable": 2}


def build_calendar_grid(slots, start_hour=8, end_hour=20):
    """Map availability slots onto an hour-by-day grid for the weekly view."""
    grid = {day: {} for day in CALENDAR_DAYS}

    for slot in slots:
        day = slot.get("day_of_week")
        if day not in grid:
            continue

        start, end = _minutes(slot.get("start_time")), _minutes(slot.get("end_time"))
        if start is None or end is None:
            continue

        availability = slot.get("availability") or "available"
        rank = AVAILABILITY_PRECEDENCE.get(availability, 0)

        for hour in range(start_hour, end_hour):
            if not ranges_overlap(start, end, hour * 60, hour * 60 + 60):
                continue
            current = grid[day].get(hour)
            if current is None or rank > AVAILABILITY_PRECEDENCE.get(current, 0):
                grid[day][hour] = availability

    return grid
