import os

import requests

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:5103")
TIMEOUT = int(os.getenv("DATABASE_TIMEOUT", "5"))


def _url(path):
    return f"{DATABASE_SERVICE_URL}{path}"


def list_rows(table, **filters):
    params = {k: v for k, v in filters.items() if v not in (None, "")}
    response = requests.get(_url(f"/{table}"), params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_row(table, row_id):
    return requests.get(_url(f"/{table}/{row_id}"), timeout=TIMEOUT)


def create_row(table, payload):
    return requests.post(_url(f"/{table}"), json=payload, timeout=TIMEOUT)


def update_row(table, row_id, payload):
    return requests.put(_url(f"/{table}/{row_id}"), json=payload, timeout=TIMEOUT)


def delete_row(table, row_id):
    return requests.delete(_url(f"/{table}/{row_id}"), timeout=TIMEOUT)


def get_timetable(staff_id):
    response = requests.get(
        _url("/timetable"), params={"staff_id": staff_id}, timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.json()
