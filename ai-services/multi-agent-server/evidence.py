import os
import re

import requests


# ============================================================
# Common Evidence Configuration
# ============================================================
#
# The Worker Agent only answers from evidence supplied here.
# Evidence is read through each feature's own backend/API
# (never another student's database), using the same base URL
# variables as the shared MCP and RAG servers. Defaults use
# 127.0.0.1: on Windows, "localhost" tries IPv6 first and adds
# about 2 seconds to every request to an IPv4-only Flask backend.

STUDENT1_BACKEND_URL = os.getenv("STUDENT1_BACKEND_URL", "http://127.0.0.1:5001")
STUDENT2_BACKEND_URL = os.getenv("STUDENT2_BACKEND_URL", "http://127.0.0.1:5002")
STUDENT3_BACKEND_URL = os.getenv("STUDENT3_BACKEND_URL", "http://127.0.0.1:5003")
STUDENT4_BACKEND_URL = os.getenv("STUDENT4_BACKEND_URL", "http://127.0.0.1:5004")
STUDENT5_BACKEND_URL = os.getenv("STUDENT5_BACKEND_URL", "http://127.0.0.1:5005")

try:
    EVIDENCE_TIMEOUT_SECONDS = float(os.getenv("EVIDENCE_TIMEOUT_SECONDS", "10"))
except ValueError:
    EVIDENCE_TIMEOUT_SECONDS = 10.0

try:
    MAX_EVIDENCE_ITEMS = int(os.getenv("MAX_EVIDENCE_ITEMS", "20"))
except ValueError:
    MAX_EVIDENCE_ITEMS = 20

# Contact details never leave a feature, matching the RAG loaders.
PRIVATE_FIELDS = {"email", "phone", "phone_number", "contact_number", "password"}


class EvidenceError(Exception):
    """A feature backend could not supply evidence."""


def fetch_json(base_url, path, params=None):
    """GET a feature backend endpoint and return its JSON body."""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    try:
        response = requests.get(url, params=params, timeout=EVIDENCE_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise EvidenceError(f"{url} is unreachable: {exc}") from exc

    if response.status_code >= 400:
        raise EvidenceError(f"{url} returned HTTP {response.status_code}")

    try:
        return response.json()
    except ValueError as exc:
        raise EvidenceError(f"{url} did not return JSON") from exc


def as_list(payload, key=None):
    """Accept either a bare JSON list or an object wrapping one."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and key and isinstance(payload.get(key), list):
        return payload[key]
    raise EvidenceError(f"unexpected response shape (expected a list{f' under {key!r}' if key else ''})")


def record_id(record, fallback):
    """Best-effort identifier for a source citation, e.g. staff_id or projectID."""
    for key, value in record.items():
        if key.lower().endswith("id") and isinstance(value, (int, str)) and value != "":
            return value
    return fallback


def evidence_item(source, record):
    """Keep scalar, non-private fields so evidence stays short and safe to prompt."""
    clean = {
        key: value
        for key, value in record.items()
        if key.lower() not in PRIVATE_FIELDS
        and not isinstance(value, (dict, list))
        and value not in (None, "")
    }
    return {"source": source, "record": clean}


def items_from(rows, source_prefix):
    return [
        evidence_item(f"{source_prefix}/{record_id(row, index)}", row)
        for index, row in enumerate(rows, start=1)
        if isinstance(row, dict)
    ]


def not_implemented(student):
    raise EvidenceError(
        f"Student {student} evidence is not implemented yet; "
        f"fill in student{student}_evidence() in multi-agent-server/evidence.py"
    )


# ============================================================
# Student 1 - Staff Management
# ============================================================
#
# OWNER: Student 1 - Andy
#
# One item per staff member, read from the Student 1 backend API
# (the same routes the RAG loader uses). Expertise, qualifications
# and availability are flattened into text on the staff record so
# the Worker can answer from a single cited source per person.

def _joined(rows, format_row):
    return "; ".join(format_row(row) for row in rows if isinstance(row, dict)) or "None recorded"


def student1_evidence():
    # /api/staff returns one row per staff/expertise pair, so de-duplicate
    staff_rows = as_list(fetch_json(STUDENT1_BACKEND_URL, "/api/staff"))
    staff_by_id = {}
    for row in staff_rows:
        if isinstance(row, dict) and row.get("staff_id") is not None:
            staff_by_id.setdefault(row["staff_id"], row)

    items = []
    for staff_id, row in staff_by_id.items():
        expertise = as_list(fetch_json(STUDENT1_BACKEND_URL, f"/api/staff/{staff_id}/expertise"))
        qualifications = as_list(fetch_json(STUDENT1_BACKEND_URL, f"/api/staff/{staff_id}/qualifications"))
        availability = as_list(fetch_json(STUDENT1_BACKEND_URL, f"/api/staff/{staff_id}/availability"))

        record = {
            "staff_id": staff_id,
            "name": row.get("name"),
            "department": row.get("department_name"),
            "position": row.get("position"),
            "employment_type": row.get("employment_type"),
            "status": row.get("status"),
            "expertise": _joined(
                expertise, lambda e: f"{e.get('expertise_area')} (skill {e.get('skill_level')}/5)"
            ),
            "qualifications": _joined(
                qualifications,
                lambda q: f"{q.get('qualification_name')}, {q.get('institution')} ({q.get('year_obtained')})",
            ),
            "availability": _joined(
                availability,
                lambda a: f"{a.get('day')} {a.get('time_slot')}: {a.get('availability_status')}",
            ),
        }
        items.append(evidence_item(f"student1/staff/{staff_id}", record))

    return items


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================
#
# OWNER: Student 2 - Hein
#
# TODO: return evidence for your feature, read through your own
# backend/API (never another student's database).
#
# Pattern:
#
# def student2_evidence():
#     rows = as_list(fetch_json(STUDENT2_BACKEND_URL, "/api/<your-route>"))
#     return items_from(rows, "student2/<resource>")
#
# Each item's source (e.g. "student2/<resource>/<id>") is what
# the Worker cites. Also update your evidence_description in
# FEATURES below.


def student2_evidence():
    context = fetch_json(
        STUDENT2_BACKEND_URL,
        "/api/rag/context",
    )

    if not isinstance(context, dict):
        raise EvidenceError(
            "Student 2 evidence must be a JSON object."
        )

    collections = {
        "subjects": "subject_code",
        "subject_offers": "offer_id",
        "classrooms": "classroom_id",
        "teaching_allocations": "allocation_id",
    }

    items = []

    for collection, id_field in collections.items():
        rows = as_list(context.get(collection))

        for index, record in enumerate(rows, start=1):
            if not isinstance(record, dict):
                continue

            record_id = record.get(id_field) or index

            items.append(
                evidence_item(
                    f"student2/{collection}/{record_id}",
                    record,
                )
            )

    return items



# ============================================================
# Student 3 - Workload & Availability Management
# ============================================================
#
# OWNER: Student 3 - Tristan
#
# Workload profiles plus open alerts, read from the Student 3
# JSON API. Alerts are labelled with the staff member's name and
# department so the Worker does not have to join records itself.

def student3_evidence():
    profiles = as_list(fetch_json(STUDENT3_BACKEND_URL, "/api/staff-workload/profiles"))
    alerts = as_list(
        fetch_json(STUDENT3_BACKEND_URL, "/api/staff-workload/alerts", params={"status": "open"})
    )

    staff = {p.get("staff_id"): p for p in profiles if isinstance(p, dict)}
    named_alerts = [
        {
            **alert,
            "staff_name": staff.get(alert.get("staff_id"), {}).get("staff_name"),
            "department": staff.get(alert.get("staff_id"), {}).get("department"),
        }
        for alert in alerts
        if isinstance(alert, dict)
    ]

    profile_items = [
        evidence_item(f"student3/profiles/{p.get('profile_id', i)}", p)
        for i, p in enumerate(profiles, start=1)
        if isinstance(p, dict)
    ]
    alert_items = [
        evidence_item(f"student3/alerts/{a.get('alert_id', i)}", a)
        for i, a in enumerate(named_alerts, start=1)
    ]
    return profile_items + alert_items


# ============================================================
# Student 4 - Research & Grant Management
# ============================================================
#
# OWNER: Student 4 - Nicholas
#
# TODO: return evidence for your feature, read through your own
# backend/API (never another student's database).
#
# Pattern:
#
# def student4_evidence():
#     rows = as_list(fetch_json(STUDENT4_BACKEND_URL, "/api/<your-route>"))
#     return items_from(rows, "student4/<resource>")
#
# Each item's source (e.g. "student4/<resource>/<id>") is what
# the Worker cites. Also update your evidence_description in
# FEATURES below.

def student4_evidence():
    not_implemented(4)


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================
#
# OWNER: Student 5 - Matthew

def student5_evidence():
    resources = {
        "performance-reviews": "reviewID",
        "development-goals": "goalID",
        "training-programs": "trainingID",
        "staff-training": "staffTrainingID",
        "development-recommendations": "recommendationID",
    }
    records = {}
    for resource, key in resources.items():
        rows = as_list(fetch_json(STUDENT5_BACKEND_URL, f"/api/{resource}"))
        if any(not isinstance(row, dict) or row.get(key) is None for row in rows):
            raise EvidenceError(f"unexpected {resource} record")
        records[resource] = rows

    staff_names = {}
    try:
        directory = as_list(
            fetch_json(STUDENT5_BACKEND_URL, "/api/integration/staff"), "staff"
        )
        for staff in directory:
            if isinstance(staff, dict) and staff.get("staff_id") and staff.get("name"):
                staff_names[staff["staff_id"]] = staff["name"]
    except EvidenceError:
        pass

    programs = {row["trainingID"]: row for row in records["training-programs"]}
    goals = {row["goalID"]: row for row in records["development-goals"]}
    items = []

    for resource, key in resources.items():
        for row in records[resource]:
            record = {
                "staffID": row.get("staffID"),
                "staffName": staff_names.get(row.get("staffID")),
                "status": row.get("status"), **row,
            }
            if resource == "development-goals":
                record = {
                    "title": row.get("title"), "progress": row.get("progress"),
                    "targetDate": row.get("targetDate"), **record,
                }
            elif resource == "training-programs":
                record = {
                    "title": row.get("title"), "skillArea": row.get("skillArea"),
                    "provider": row.get("provider"), **record,
                }
            elif resource == "staff-training":
                program = programs.get(row.get("trainingID"), {})
                record = {"trainingTitle": program.get("title"), **record}
            elif resource == "development-recommendations":
                goal = goals.get(row.get("goalID"), {})
                record = {
                    "actionState": "Proposed recommendation",
                    "staffID": row.get("staffID"), "status": row.get("status"),
                    "goalTitle": goal.get("title"),
                    "recommendation": row.get("recommendation"), **record,
                }
            items.append(evidence_item(f"student5/{resource}/{row[key]}", record))

    return items


# ============================================================
# Feature Registry
# ============================================================
#
# Each backend sends its own feature key with a workflow
# request, so the Worker only sees that feature's evidence.

FEATURES = {
    "student1": {
        "name": "Academic Staff Management",
        "owner": "Andy Lam",
        "evidence_description": (
            "one record per staff member: department, position, employment type, "
            "status, expertise areas with skill level (1-5), qualifications and "
            "weekly availability"
        ),
        "collect": student1_evidence,
    },
    "student2": {
        "name": "Teaching, Subject and Classroom Allocation",
        "owner": "Hein Htet Aung",
        "evidence_description": (
            "subject records, subject offers, classroom capacities "
            "and facilities, teaching allocations, schedules and staff assignments"
        ),
        "collect": student2_evidence,
    },
    "student3": {
        "name": "Workload and Availability Management",
        "owner": "Tristan Lim",
        "evidence_description": "staff workload profiles (hours, caps, status) and open workload alerts",
        "collect": student3_evidence,
    },
    "student4": {
        "name": "Research and Grant Management",
        "owner": "Nicholas Hatzidimitriou",
        "evidence_description": "TODO: describe the evidence your section supplies",
        "collect": student4_evidence,
    },
    "student5": {
        "name": "Performance and Professional Development",
        "owner": "Matthew Barnard",
        "evidence_description": (
            "performance reviews, development goals with progress and target dates, "
            "training programs, staff enrolments with program titles, and proposed "
            "development recommendations with related goals and decision status"
        ),
        "collect": student5_evidence,
    },
}


def normalise_feature(value):
    """Accept 'student3', 'Student 3' or 3; return a FEATURES key or None."""
    if value is None:
        return None
    key = re.sub(r"[\s_-]", "", str(value)).lower()
    if key.isdigit():
        key = f"student{key}"
    return key if key in FEATURES else None


def describe_features():
    return {
        key: {name: value for name, value in meta.items() if name != "collect"}
        for key, meta in FEATURES.items()
    }


def _words(text):
    return set(re.findall(r"[a-z0-9]+", str(text).lower()))


def select_relevant(items, user_request, limit=MAX_EVIDENCE_ITEMS):
    """Keep the items sharing the most words with the request (original order on ties)."""
    request_words = _words(user_request)
    scored = [
        (len(request_words & _words(" ".join(map(str, item["record"].values())))), index, item)
        for index, item in enumerate(items)
    ]
    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    return [item for _, _, item in scored[:limit]]


def collect_evidence(feature_key, user_request):
    """Return (evidence_items, total_available). Raises EvidenceError on failure."""
    items = FEATURES[feature_key]["collect"]()
    return select_relevant(items, user_request), len(items)
