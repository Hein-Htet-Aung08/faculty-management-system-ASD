import os

import requests


STAFF_SERVICE_URL = os.getenv(
    "STAFF_SERVICE_URL",
    "http://staff-backend:5001",
)


def get_staff():
    response = requests.get(
        f"{STAFF_SERVICE_URL}/api/staff",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_staff_by_id_response(staff_id):
    return requests.get(
        f"{STAFF_SERVICE_URL}/api/staff/{staff_id}",
        timeout=5,
    )


def get_staff_expertise_response(staff_id):
    return requests.get(
        f"{STAFF_SERVICE_URL}/api/staff/{staff_id}/expertise",
        timeout=5,
    )