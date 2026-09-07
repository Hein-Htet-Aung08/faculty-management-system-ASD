import os

import requests

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:5105").rstrip("/")
DATABASE_TIMEOUT = float(os.getenv("DATABASE_TIMEOUT", "5"))


def request_resource(method, resource, row_id=None, filters=None, payload=None):
    path = f"/{resource}"
    if row_id is not None:
        path += f"/{row_id}"
    return requests.request(
        method,
        f"{DATABASE_SERVICE_URL}{path}",
        params=filters or None,
        json=payload,
        timeout=DATABASE_TIMEOUT,
    )


def read_json(response):
    response.raise_for_status()
    return response.json()


def list_resource(resource, filters=None):
    return request_resource("GET", resource, filters=filters)


def get_resource(resource, row_id):
    return request_resource("GET", resource, row_id=row_id)


def create_resource(resource, payload):
    return request_resource("POST", resource, payload=payload)


def update_resource(resource, row_id, payload):
    return request_resource("PUT", resource, row_id=row_id, payload=payload)


def delete_resource(resource, row_id):
    return request_resource("DELETE", resource, row_id=row_id)
