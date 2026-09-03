import os

import requests

STAFF_SERVICE_URL = os.getenv("STAFF_SERVICE_URL", "http://staff-backend:5001")
TIMEOUT = float(os.getenv("STAFF_TIMEOUT", "5"))


class StaffServiceUnavailable(RuntimeError):
    """Raised when the staff service cannot be reached or returns an error."""


def _get(path, params=None):
    try:
        response = requests.get(f"{STAFF_SERVICE_URL}{path}", params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise StaffServiceUnavailable(str(exc)) from exc


def list_staff():
    """The full roster. One row per staff/expertise pair, so ids can repeat."""
    return _get("/api/staff")


def get_staff(staff_id):
    """One staff member, or None when the service reports 404."""
    try:
        response = requests.get(
            f"{STAFF_SERVICE_URL}/api/staff/{staff_id}", timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        raise StaffServiceUnavailable(str(exc)) from exc

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise StaffServiceUnavailable(f"{response.status_code} from staff service")
    return response.json()


def search_by_expertise(expertise):
    return _get("/api/staff/search", {"expertise": expertise})


def list_departments():
    return _get("/api/departments")


def staff_directory():
    directory = {}

    for row in list_staff():
        staff_id = row.get("staff_id")
        entry = directory.setdefault(staff_id, {
            "staff_id": staff_id,
            "name": row.get("name"),
            "department_name": row.get("department_name"),
            "position": row.get("position"),
            "employment_type": row.get("employment_type"),
            "status": row.get("status"),
            "expertise": [],
        })
        area = row.get("expertise_area")
        if area and area not in entry["expertise"]:
            entry["expertise"].append(area)

    return [directory[key] for key in sorted(directory)]


def name_lookup():
    """staff_id -> name, for labelling workload rows with the authoritative name.

    Returns an empty mapping when the staff service is unavailable so callers
    can fall back to their own stored names.
    """
    try:
        return {entry["staff_id"]: entry["name"] for entry in staff_directory()}
    except StaffServiceUnavailable:
        return {}
