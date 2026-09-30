import os

import requests


# ============================================================
# Common MCP Configuration
# ============================================================

STUDENT1_BACKEND_URL = os.getenv(
    "STUDENT1_BACKEND_URL",
    "http://localhost:5001",
)

STUDENT2_BACKEND_URL = os.getenv(
    "STUDENT2_BACKEND_URL",
    "http://localhost:5002",
)

STUDENT3_BACKEND_URL = os.getenv(
    "STUDENT3_BACKEND_URL",
    "http://localhost:5003",
)

STUDENT4_BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL",
    "http://localhost:5004",
)

STUDENT5_BACKEND_URL = os.getenv(
    "STUDENT5_BACKEND_URL",
    "http://localhost:5005",
)


try:
    MCP_TOOL_TIMEOUT_SECONDS = float(
        os.getenv(
            "MCP_TOOL_TIMEOUT_SECONDS",
            "10",
        )
    )
except ValueError:
    MCP_TOOL_TIMEOUT_SECONDS = 10.0


def call_feature_api(
    method,
    base_url,
    path,
    *,
    params=None,
    json_body=None,
):
    """
    Common helper used by MCP tools to call a student feature backend.

    MCP tools should access feature data and business logic through
    the appropriate feature backend/API instead of directly accessing
    another student's database.

    Returns a structured dictionary for both success and failure.
    """

    url = (
        f"{base_url.rstrip('/')}"
        f"/{path.lstrip('/')}"
    )

    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            timeout=MCP_TOOL_TIMEOUT_SECONDS,
        )

    except requests.RequestException as exc:
        return {
            "status": "error",
            "error": "feature_service_unavailable",
            "details": str(exc),
            "url": url,
        }

    try:
        payload = response.json()

    except ValueError:
        payload = {
            "raw": response.text,
        }

    if response.status_code >= 400:
        return {
            "status": "error",
            "http_status": response.status_code,
            "url": url,
            "data": payload,
        }

    return {
        "status": "success",
        "http_status": response.status_code,
        "url": url,
        "data": payload,
    }


# ============================================================
# Student 1 - Staff Management
# ============================================================
#
# OWNER: Student 1
#
# Add Student 1 MCP tool implementation functions here.
#
# Guidelines:
# - Use STUDENT1_BACKEND_URL.
# - Reuse existing Staff Management backend/API behaviour.
# - Return structured dictionaries.
# - Do not directly access another feature's database.
# - Keep each tool boundary narrow and explicit.
#
# Example naming convention:
#
# def student1_<tool_name>(...):
#     return call_feature_api(
#         "GET",
#         STUDENT1_BACKEND_URL,
#         "/...",
#     )
#


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================
#
# OWNER: Student 2 - Hein
#
# Student 2 MCP tools reuse the existing allocation backend/API.
# Business rules remain inside the Student 2 feature backend rather
# than being duplicated inside the shared MCP server.
#


def student2_validate_teaching_allocation(
    offer_id: str,
    classroom_id: str,
    day: str,
    date_range: str,
    start_time: str,
    end_time: str,
    class_type: str,
    expected_class_size: int,
    assigned_staff_member: int | None = None,
    allocation_status: str | None = None,
):
    """
    Validate a proposed teaching allocation using Student 2's
    existing allocation validation rules.

    This tool does not create or update an allocation.
    """

    allocation = {
        "offer_id": offer_id,
        "classroom_id": classroom_id,
        "day": day,
        "date_range": date_range,
        "start_time": start_time,
        "end_time": end_time,
        "class_type": class_type,
        "expected_class_size": expected_class_size,
    }

    if assigned_staff_member is not None:
        allocation[
            "assigned_staff_member"
        ] = assigned_staff_member

    if allocation_status is not None:
        allocation[
            "allocation_status"
        ] = allocation_status

    return call_feature_api(
        "POST",
        STUDENT2_BACKEND_URL,
        "/teaching-allocations/validate",
        json_body=allocation,
    )


def student2_check_classroom_availability(
    classroom_id: str,
    date: str,
    year: int,
    start_time: str,
    end_time: str,
):
    """
    Check whether one classroom is available for a specific
    date and time using Student 2's existing scheduling rules.

    This tool does not reserve or modify the classroom.
    """

    return call_feature_api(
        "GET",
        STUDENT2_BACKEND_URL,
        "/classrooms/available",
        params={
            "classroom_id":
                classroom_id,
            "date":
                date,
            "year":
                year,
            "start_time":
                start_time,
            "end_time":
                end_time,
        },
    )


# ============================================================
# Student 3 - Workload & Availability Management
# ============================================================
#
# OWNER: Student 3
#
# Reads go through STUDENT3_BACKEND_URL (the feature's own Flask
# backend, at its /api/staff-workload/* JSON endpoints) rather than
# its database directly, per the shared convention above.
#

def student3_staff_count(status=None, department=None):
    params = {k: v for k, v in {"status": status, "department": department}.items() if v}
    result = call_feature_api(
        "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/profiles", params=params
    )
    if result["status"] != "success":
        return result
    return {"status": "success", "data": {"count": len(result["data"])}}


def student3_staff_by_status(status: str):
    return call_feature_api(
        "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/profiles", params={"status": status}
    )


def student3_staff_workload_detail(staff_id: int):
    result = call_feature_api(
        "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/profiles"
    )
    if result["status"] != "success":
        return result

    match = next((row for row in result["data"] if row.get("staff_id") == staff_id), None)
    if match is None:
        return {"status": "error", "error": f"staff_id {staff_id} not found"}
    return {"status": "success", "data": match}


def student3_open_alerts(department: str | None = None):
    result = call_feature_api(
        "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/alerts", params={"status": "open"}
    )
    if result["status"] != "success":
        return result

    alerts = result["data"]
    if department:
        profiles_result = call_feature_api(
            "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/profiles", params={"department": department}
        )
        if profiles_result["status"] == "success":
            allowed_ids = {row["staff_id"] for row in profiles_result["data"]}
            alerts = [a for a in alerts if a.get("staff_id") in allowed_ids]

    return {"status": "success", "data": alerts}
#


# ============================================================
# Student 4 - Research & Grant Management
# ============================================================
#
# OWNER: Student 4
#
# Adapted from the Student 4 Release 1 MCP tools. Reads go through
# STUDENT4_BACKEND_URL (the feature's own Flask backend) rather than
# its database directly, per the shared convention above.
#

def student4_project_count(department=None, status=None):
    params = {k: v for k, v in {"department": department, "status": status}.items() if v is not None}
    result = call_feature_api("GET", STUDENT4_BACKEND_URL, "/projects", params=params)
    if result["status"] != "success":
        return result
    return {"status": "success", "data": {"count": len(result["data"])}}


def student4_projects_by_department(department: str):
    return call_feature_api(
        "GET", STUDENT4_BACKEND_URL, "/projects", params={"department": department}
    )


def student4_project_grants_summary(project_id: int):
    project_result = call_feature_api("GET", STUDENT4_BACKEND_URL, f"/projects/{project_id}")
    if project_result["status"] != "success":
        return project_result

    grants_result = call_feature_api(
        "GET", STUDENT4_BACKEND_URL, f"/projects/{project_id}/grants"
    )
    if grants_result["status"] != "success":
        return grants_result

    project = project_result["data"]
    grants = grants_result["data"]
    total_requested = sum(g.get("amountRequested") or 0 for g in grants)
    total_awarded = sum(g.get("amountAwarded") or 0 for g in grants)

    return {
        "status": "success",
        "data": {
            "projectID": project_id,
            "title": project.get("title"),
            "grantCount": len(grants),
            "totalRequested": total_requested,
            "totalAwarded": total_awarded,
            "grants": grants,
        },
    }


def student4_research_history(department: str):
    projects_result = call_feature_api(
        "GET", STUDENT4_BACKEND_URL, "/projects", params={"department": department}
    )
    if projects_result["status"] != "success":
        return projects_result

    history = []
    for project in projects_result["data"]:
        project_id = project.get("projectID")
        analyses_result = call_feature_api(
            "GET", STUDENT4_BACKEND_URL, "/ai-analysis", params={"projectID": project_id}
        )
        summaries = []
        if analyses_result["status"] == "success":
            summaries = [
                a["generatedSummary"] for a in analyses_result["data"] if a.get("generatedSummary")
            ]
        history.append({"projectID": project_id, "title": project.get("title"), "summaries": summaries})

    return {"status": "success", "data": history}


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================
#
# OWNER: Student 5
#
# Add Student 5 MCP tool implementation functions here.
#
# Use STUDENT5_BACKEND_URL where appropriate.
#