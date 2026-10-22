"""Release 2 Multi-Agent routes. The shared server is never contacted: it is
either disabled (as in CI) or replaced with a fake."""

import pytest

import ai_services_client as ai_services

CLOSED_PORT_URL = "http://127.0.0.1:9"

WORKFLOW = {
    "workflow_id": "wf-1",
    "feature": "student1",
    "status": "awaiting_human_review",
    "human_decision": {"status": "pending"},
}


@pytest.fixture
def multi_agent_on(monkeypatch):
    monkeypatch.setattr(ai_services, "MULTI_AGENT_ENABLED", True)


@pytest.fixture
def fake_server(monkeypatch, multi_agent_on):
    """Records each forwarded call and replies from a {(method, path): (body, status)} table."""
    calls = []
    replies = {}

    def fake_call(method, path, timeout=None, **kwargs):
        calls.append((method, path, kwargs))
        return replies.get((method, path), ({"error": "not found"}, 404))

    monkeypatch.setattr(ai_services, "call_multi_agent", fake_call)
    return calls, replies


# ---------- disabled (CI default) ----------

@pytest.mark.parametrize("method, path, body", [
    ("post", "/api/multi-agent/workflow", {"user_request": "Who knows cloud?"}),
    ("get", "/api/multi-agent/workflow/history", None),
    ("get", "/api/multi-agent/workflow/wf-1", None),
    ("post", "/api/multi-agent/workflow/wf-1/decision", {"decision": "Accept"}),
])
def test_routes_return_503_when_disabled(client, method, path, body):
    response = getattr(client, method)(path, json=body)

    assert response.status_code == 503
    assert "disabled" in response.json["error"]


# ---------- enabled, server faked ----------

def test_run_sends_trimmed_request_with_own_feature_key(client, fake_server):
    calls, replies = fake_server
    replies[("POST", "workflow")] = (WORKFLOW, 200)

    response = client.post("/api/multi-agent/workflow", json={"user_request": "  Who knows cloud?  "})

    assert response.status_code == 200
    assert response.json["workflow_id"] == "wf-1"
    assert calls[0][2]["json"] == {"user_request": "Who knows cloud?", "feature": "student1"}


def test_run_rejects_empty_request_before_calling_server(client, fake_server):
    calls, _ = fake_server

    assert client.post("/api/multi-agent/workflow", json={"user_request": "  "}).status_code == 400
    assert calls == []


def test_history_is_filtered_to_staff_management(client, fake_server):
    calls, replies = fake_server
    replies[("GET", "workflow/history")] = ({"status": "success", "workflows": [WORKFLOW]}, 200)

    response = client.get("/api/multi-agent/workflow/history?limit=5")

    assert response.status_code == 200
    assert calls[0][2]["params"] == {"feature": "student1", "limit": "5"}


def test_other_features_workflows_are_hidden(client, fake_server):
    _, replies = fake_server
    replies[("GET", "workflow/wf-2")] = ({**WORKFLOW, "workflow_id": "wf-2", "feature": "student3"}, 200)

    assert client.get("/api/multi-agent/workflow/wf-2").status_code == 404


def test_decision_forwards_only_decision_fields(client, fake_server):
    calls, replies = fake_server
    replies[("GET", "workflow/wf-1")] = (WORKFLOW, 200)
    replies[("POST", "workflow/wf-1/decision")] = ({**WORKFLOW, "status": "accepted"}, 200)

    response = client.post("/api/multi-agent/workflow/wf-1/decision", json={
        "decision": "Accept", "reviewer": "Andy", "notes": "Looks right", "feature": "student3",
    })

    assert response.status_code == 200
    assert calls[-1][2]["json"] == {"decision": "Accept", "reviewer": "Andy", "notes": "Looks right"}


def test_decision_conflict_is_passed_through(client, fake_server):
    _, replies = fake_server
    replies[("GET", "workflow/wf-1")] = (WORKFLOW, 200)
    replies[("POST", "workflow/wf-1/decision")] = ({"error": "already decided"}, 409)

    response = client.post("/api/multi-agent/workflow/wf-1/decision", json={"decision": "Accept"})

    assert response.status_code == 409


def test_unreachable_server_returns_503(client, multi_agent_on, monkeypatch):
    monkeypatch.setattr(ai_services, "MULTI_AGENT_SERVER_URL", CLOSED_PORT_URL)

    response = client.get("/api/multi-agent/workflow/history")

    assert response.status_code == 503
    assert "Could not reach Multi-Agent server" in response.json["error"]
