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
# TODO: return evidence for your feature, read through your own
# backend/API (never another student's database).
#
# Pattern:
#
# def student1_evidence():
#     rows = as_list(fetch_json(STUDENT1_BACKEND_URL, "/api/<your-route>"))
#     return items_from(rows, "student1/<resource>")
#
# Each item's source (e.g. "student1/<resource>/<id>") is what
# the Worker cites. Also update your evidence_description in
# FEATURES below.

def student1_evidence():
    not_implemented(1)


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

def student4_evidence():
    projects = as_list(fetch_json(STUDENT4_BACKEND_URL, "/projects"))

    grant_items = []
    for project in projects:
        project_id = project.get("projectID")
        if project_id is None:
            continue
        grants = as_list(fetch_json(STUDENT4_BACKEND_URL, f"/projects/{project_id}/grants"))
        grant_items.extend(
            evidence_item(
                f"student4/grants/{grant.get('grantID', index)}",
                {**grant, "projectTitle": project.get("title")},
            )
            for index, grant in enumerate(grants, start=1)
            if isinstance(grant, dict)
        )

    analyses = as_list(fetch_json(STUDENT4_BACKEND_URL, "/ai-analysis"))

    project_items = items_from(projects, "student4/projects")
    analysis_items = items_from(analyses, "student4/research_history")
    return project_items + grant_items + analysis_items


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================
#
# OWNER: Student 5 - Matthew
#
# TODO: return evidence for your feature, read through your own
# backend/API (never another student's database).
#
# Pattern:
#
# def student5_evidence():
#     rows = as_list(fetch_json(STUDENT5_BACKEND_URL, "/api/<your-route>"))
#     return items_from(rows, "student5/<resource>")
#
# Each item's source (e.g. "student5/<resource>/<id>") is what
# the Worker cites. Also update your evidence_description in
# FEATURES below.

def student5_evidence():
    not_implemented(5)


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
        "evidence_description": "TODO: describe the evidence your section supplies",
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
        "evidence_description": "research projects, their grants (funding body, amounts, status), "
                                 "and AI-generated research history summaries",
        "collect": student4_evidence,
    },
    "student5": {
        "name": "Performance and Professional Development",
        "owner": "Matthew Barnard",
        "evidence_description": "TODO: describe the evidence your section supplies",
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
