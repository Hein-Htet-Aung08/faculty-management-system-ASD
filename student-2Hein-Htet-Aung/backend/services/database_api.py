import os

import requests


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://database-service:6002",
)


def get_subjects():
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/subjects",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_subject_by_code_response(subject_code):
    return requests.get(
        f"{DATABASE_SERVICE_URL}/subjects/{subject_code}",
        timeout=5,
    )


def create_subject_response(data):
    return requests.post(
        f"{DATABASE_SERVICE_URL}/subjects",
        json=data,
        timeout=5,
    )


def update_subject_response(subject_code, data):
    return requests.put(
        f"{DATABASE_SERVICE_URL}/subjects/{subject_code}",
        json=data,
        timeout=5,
    )


def delete_subject_response(subject_code):
    return requests.delete(
        f"{DATABASE_SERVICE_URL}/subjects/{subject_code}",
        timeout=5,
    )


def get_subject_offers():
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/subject-offers",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_subject_offer_by_id_response(offer_id):
    return requests.get(
        f"{DATABASE_SERVICE_URL}/subject-offers/{offer_id}",
        timeout=5,
    )


def create_subject_offer_response(data):
    return requests.post(
        f"{DATABASE_SERVICE_URL}/subject-offers",
        json=data,
        timeout=5,
    )


def update_subject_offer_response(offer_id, data):
    return requests.put(
        f"{DATABASE_SERVICE_URL}/subject-offers/{offer_id}",
        json=data,
        timeout=5,
    )


def delete_subject_offer_response(offer_id):
    return requests.delete(
        f"{DATABASE_SERVICE_URL}/subject-offers/{offer_id}",
        timeout=5,
    )


def get_classrooms():
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/classrooms",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_classroom_by_id_response(classroom_id):
    return requests.get(
        f"{DATABASE_SERVICE_URL}/classrooms/{classroom_id}",
        timeout=5,
    )


def create_classroom_response(data):
    return requests.post(
        f"{DATABASE_SERVICE_URL}/classrooms",
        json=data,
        timeout=5,
    )


def update_classroom_response(classroom_id, data):
    return requests.put(
        f"{DATABASE_SERVICE_URL}/classrooms/{classroom_id}",
        json=data,
        timeout=5,
    )


def delete_classroom_response(classroom_id):
    return requests.delete(
        f"{DATABASE_SERVICE_URL}/classrooms/{classroom_id}",
        timeout=5,
    )


def get_teaching_allocations():
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/teaching-allocations",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def get_teaching_allocation_by_id_response(allocation_id):
    return requests.get(
        f"{DATABASE_SERVICE_URL}/teaching-allocations/{allocation_id}",
        timeout=5,
    )


def create_teaching_allocation_response(data):
    return requests.post(
        f"{DATABASE_SERVICE_URL}/teaching-allocations",
        json=data,
        timeout=5,
    )


def update_teaching_allocation_response(allocation_id, data):
    return requests.put(
        f"{DATABASE_SERVICE_URL}/teaching-allocations/{allocation_id}",
        json=data,
        timeout=5,
    )


def delete_teaching_allocation_response(allocation_id):
    return requests.delete(
        f"{DATABASE_SERVICE_URL}/teaching-allocations/{allocation_id}",
        timeout=5,
    )