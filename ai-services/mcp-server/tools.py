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

def student1_get_staff_profile(
    staff_id,
):
    """
    Return one staff member's full profile: core details,
    expertise, qualifications and weekly availability.

    Read only. Combines four Staff Management API calls into
    one structured result.
    """

    if (
        not isinstance(staff_id, int)
        or isinstance(staff_id, bool)
        or staff_id < 1
    ):
        return {
            "status": "error",
            "error": "invalid_input",
            "details": "staff_id must be a positive integer.",
        }

    profile = call_feature_api(
        "GET",
        STUDENT1_BACKEND_URL,
        f"/api/staff/{staff_id}",
    )

    if profile["status"] != "success":
        return profile

    sections = {}

    for section in (
        "expertise",
        "qualifications",
        "availability",
    ):
        result = call_feature_api(
            "GET",
            STUDENT1_BACKEND_URL,
            f"/api/staff/{staff_id}/{section}",
        )

        if result["status"] != "success":
            return result

        sections[section] = result["data"]

    return {
        "status": "success",
        "tool": "student1_get_staff_profile",
        "data": {
            "staff": profile["data"],
            **sections,
        },
    }


def student1_search_staff_by_expertise(
    expertise,
):
    """
    Find staff whose expertise area matches the given text
    (case-insensitive partial match).

    Read only. Returns each match's department, position,
    status, expertise area and skill level (1-5).
    """

    expertise = (
        expertise
        if isinstance(expertise, str)
        else ""
    ).strip()

    if not expertise:
        return {
            "status": "error",
            "error": "invalid_input",
            "details": "expertise must be a non-empty string.",
        }

    result = call_feature_api(
        "GET",
        STUDENT1_BACKEND_URL,
        "/api/staff/search",
        params={
            "expertise": expertise,
        },
    )

    if result["status"] != "success":
        return result

    return {
        "status": "success",
        "tool": "student1_search_staff_by_expertise",
        "query": expertise,
        "match_count": len(result["data"]),
        "data": result["data"],
    }


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================
#
# OWNER: Student 2 - Hein
#
# Add Student 2 MCP tool implementation functions here.
#
# Existing Student 2 APIs that are suitable for MCP include:
#
# POST /teaching-allocations/validate
# GET  /classrooms/available
#
# Initial planned MCP tools:
#
# student2_validate_teaching_allocation
# student2_check_classroom_availability
#
# Use STUDENT2_BACKEND_URL.
# Reuse Student 2 backend validation/business rules rather than
# duplicating allocation logic inside this shared MCP service.
#


# ============================================================
# Student 3 - Workload & Availability Management
# ============================================================
#
# OWNER: Student 3
#
# Add Student 3 MCP tool implementation functions here.
#
# Student 3 may adapt the MCP tool work already implemented in
# their Release 1 branch into this shared server.
#
# Use STUDENT3_BACKEND_URL where appropriate.
#


# ============================================================
# Student 4 - Research & Grant Management
# ============================================================
#
# OWNER: Student 4
#
# Add Student 4 MCP tool implementation functions here.
#
# Student 4 may adapt the MCP tool work already implemented in
# their Release 1 branch into this shared server.
#
# Use STUDENT4_BACKEND_URL where appropriate.
#


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