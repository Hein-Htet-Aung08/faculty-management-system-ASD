
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app
from routes import allocations as allocation_routes
from routes import classrooms as classroom_routes
from routes import ai_mode as ai_mode_routes
from routes import multi_agent_mode as multi_agent_routes

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

def test_ai_mode_disabled(client, monkeypatch):
    monkeypatch.setattr(
        ai_mode_routes.llm_client,
        "AI_MODE_ENABLED",
        False,
    )

    response = client.post(
        "/teaching-allocations/recommend",
        json={"offer_id": "41114_SPR_2026"},
    )

    assert response.status_code == 503
    assert response.get_json()["error"] == "AI-Mode is disabled"


def test_multi_agent_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("MULTI_AGENT_ENABLED", raising=False)

    response = client.post(
        "/multi-agent/workflow",
        json={"user_request": "Review classroom allocations"},
    )

    assert response.status_code == 403


def test_multi_agent_forces_student2_feature(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["payload"] = kwargs["json"]

        return SimpleNamespace(
            status_code=200,
            json=lambda: {"status": "awaiting_human_review"},
        )

    monkeypatch.setattr(
        multi_agent_routes.requests,
        "request",
        fake_request,
    )

    response = client.post(
        "/multi-agent/workflow",
        json={
            "user_request": "Review teaching allocations",
            "feature": "student3",
        },
    )

    assert response.status_code == 200
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/workflow")
    assert captured["payload"] == {
        "user_request": "Review teaching allocations",
        "feature": "student2",
    }


def test_multi_agent_history_is_student2_only(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["params"] = kwargs["params"]

        return SimpleNamespace(
            status_code=200,
            json=lambda: {"status": "success", "workflows": []},
        )

    monkeypatch.setattr(
        multi_agent_routes.requests,
        "request",
        fake_request,
    )

    response = client.get("/multi-agent/workflow/history")

    assert response.status_code == 200
    assert captured["params"]["feature"] == "student2"


def test_multi_agent_blocks_foreign_workflow_decision(
    client, monkeypatch
):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(method)

        return SimpleNamespace(
            status_code=200,
            json=lambda: {"feature": "student3"},
        )

    monkeypatch.setattr(
        multi_agent_routes.requests,
        "request",
        fake_request,
    )

    response = client.post(
        "/multi-agent/workflow/test-id/decision",
        json={"decision": "Accept", "reviewer": "Tester"},
    )

    assert response.status_code == 404
    assert calls == ["GET"]


def test_multi_agent_forwards_human_decision(
    client, monkeypatch
):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    forwarded = {}

    def fake_request(method, url, **kwargs):
        if method == "GET":
            return SimpleNamespace(
                status_code=200,
                json=lambda: {"feature": "student2"},
            )

        forwarded["body"] = kwargs["json"]

        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "feature": "student2",
                "status": "accepted",
            },
        )

    monkeypatch.setattr(
        multi_agent_routes.requests,
        "request",
        fake_request,
    )

    response = client.post(
        "/multi-agent/workflow/test-id/decision",
        json={
            "decision": "Accept",
            "reviewer": "Tester",
            "notes": "Evidence reviewed",
        },
    )

    assert response.status_code == 200
    assert forwarded["body"] == {
        "decision": "Accept",
        "reviewer": "Tester",
        "notes": "Evidence reviewed",
    }
