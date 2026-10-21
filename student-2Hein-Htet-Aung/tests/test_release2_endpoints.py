
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from routes import allocations as allocation_routes
from routes import classrooms as classroom_routes


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def allocation_data():
    return {
        "offer_id": "41114_SPR_2026",
        "assigned_staff_member": None,
        "classroom_id": "CB11.04.406",
        "day": "THU",
        "date_range": "03/08 - 20/09",
        "start_time": "14:00",
        "end_time": "16:00",
        "class_type": "TUT",
        "expected_class_size": 30,
        "allocation_status": "NEEDS_ASSIGNMENT",
    }


@pytest.fixture
def occupied_allocation():
    return {
        "allocation_id": 4,
        "classroom_id": "CB11.04.406",
        "day": "THU",
        "date_range": "03/08 - 20/09",
        "start_time": "14:00",
        "end_time": "16:00",
        "allocation_status": "NEEDS_ASSIGNMENT",
    }


def mock_validation_context(
    monkeypatch,
    allocations=None,
    capacity=30,
):
    def load_context(data):
        subject_offer = {
            "offer_id": "41114_SPR_2026",
            "year": "2026",
        }

        classroom = {
            "classroom_id": "CB11.04.406",
            "capacity": capacity,
        }

        return (
            subject_offer,
            classroom,
            allocations or [],
            None,
            False,
            None,
        )

    monkeypatch.setattr(
        allocation_routes,
        "load_validation_context",
        load_context,
    )


# Endpoint 1: POST /teaching-allocations/validate

def test_validation_accepts_valid_allocation(
    client, monkeypatch, allocation_data
):
    mock_validation_context(monkeypatch)

    response = client.post(
        "/teaching-allocations/validate",
        json=allocation_data,
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "valid": True,
        "errors": [],
    }


def test_validation_rejects_oversized_class(
    client, monkeypatch, allocation_data
):
    mock_validation_context(monkeypatch, capacity=30)

    allocation_data["expected_class_size"] = 31

    response = client.post(
        "/teaching-allocations/validate",
        json=allocation_data,
    )

    result = response.get_json()

    assert response.status_code == 200
    assert result["valid"] is False
    assert (
        "Classroom capacity is smaller than the expected class size."
        in result["errors"]
    )


def test_validation_rejects_classroom_conflict(
    client, monkeypatch, allocation_data, occupied_allocation
):
    mock_validation_context(
        monkeypatch,
        allocations=[occupied_allocation],
    )

    response = client.post(
        "/teaching-allocations/validate",
        json=allocation_data,
    )

    result = response.get_json()

    assert response.status_code == 200
    assert result["valid"] is False
    assert (
        "Classroom is unavailable during one or more requested dates."
        in result["errors"]
    )


def test_validation_rejects_missing_payload(client):
    response = client.post(
        "/teaching-allocations/validate",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["valid"] is False


# Endpoint 2: GET /classrooms/available

def mock_classroom_dependencies(monkeypatch, allocations):
    classroom_response = SimpleNamespace(
        status_code=200,
        raise_for_status=lambda: None,
    )

    monkeypatch.setattr(
        classroom_routes,
        "get_classroom_by_id_response",
        lambda classroom_id: classroom_response,
    )

    monkeypatch.setattr(
        classroom_routes,
        "get_teaching_allocations",
        lambda: allocations,
    )


def test_classroom_available_after_existing_class(
    client, monkeypatch, occupied_allocation
):
    mock_classroom_dependencies(
        monkeypatch,
        [occupied_allocation],
    )

    response = client.get(
        "/classrooms/available",
        query_string={
            "classroom_id": "CB11.04.406",
            "date": "10/09",
            "year": "2026",
            "start_time": "16:00",
            "end_time": "18:00",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["available"] is True


def test_classroom_unavailable_during_existing_class(
    client, monkeypatch, occupied_allocation
):
    mock_classroom_dependencies(
        monkeypatch,
        [occupied_allocation],
    )

    response = client.get(
        "/classrooms/available",
        query_string={
            "classroom_id": "CB11.04.406",
            "date": "10/09",
            "year": "2026",
            "start_time": "14:30",
            "end_time": "15:30",
        },
    )

    result = response.get_json()

    assert response.status_code == 200
    assert result["available"] is False
    assert result["conflicting_allocation_id"] == 4


def test_classroom_requires_valid_year(client):
    response = client.get(
        "/classrooms/available",
        query_string={
            "classroom_id": "CB11.04.406",
            "date": "10/09",
            "start_time": "14:00",
            "end_time": "16:00",
        },
    )

    assert response.status_code == 400
    assert "year" in response.get_json()["error"].lower()
