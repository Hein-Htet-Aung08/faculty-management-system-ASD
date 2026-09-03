import os

import requests

STAFF_SERVICE_URL = os.getenv("STAFF_SERVICE_URL", "").rstrip("/")
STAFF_TIMEOUT = float(os.getenv("STAFF_TIMEOUT", "3"))


def list_staff():
    if not STAFF_SERVICE_URL:
        return []
    response = requests.get(f"{STAFF_SERVICE_URL}/api/staff", timeout=STAFF_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_staff_context(staff_id):
    if not STAFF_SERVICE_URL:
        return None

    profile_response = requests.get(
        f"{STAFF_SERVICE_URL}/api/staff/{staff_id}", timeout=STAFF_TIMEOUT
    )
    if profile_response.status_code == 404:
        return None
    profile_response.raise_for_status()

    expertise_response = requests.get(
        f"{STAFF_SERVICE_URL}/api/staff/{staff_id}/expertise", timeout=STAFF_TIMEOUT
    )
    expertise_response.raise_for_status()
    return {
        "profile": profile_response.json(),
        "expertise": expertise_response.json(),
    }
