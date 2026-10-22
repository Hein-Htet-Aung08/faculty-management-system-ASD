from unittest.mock import patch

WORKFLOW_ID = "30122189-7d44-4b1d-9a51-1f1f2f2c0a11"


def test_workflow_is_403_when_multi_agent_disabled(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "false")
    response = client.post("/multi-agent/workflow", json={"user_request": "Who is overloaded?"})

    assert response.status_code == 403
    assert "Multi-Agent mode is off" in response.get_json()["error"]


def test_status_reports_disabled_without_calling_the_server(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "false")
    with patch("routes.multi_agent_mode.server_health") as health:
        response = client.get("/multi-agent/status")

    assert response.get_json() == {"enabled": False, "feature": "student3"}
    health.assert_not_called()


def test_workflow_always_sends_the_student3_feature(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    with patch("routes.multi_agent_mode.run_workflow", return_value=({"status": "awaiting_human_review"}, 200)) as run:
        response = client.post("/multi-agent/workflow", json={"user_request": " Who is overloaded? ", "feature": "student1"})

    assert response.status_code == 200
    run.assert_called_once_with("Who is overloaded?")


def test_blank_request_is_400(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    response = client.post("/multi-agent/workflow", json={"user_request": "  "})

    assert response.status_code == 400


def test_workflow_id_must_be_a_uuid(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    with patch("routes.multi_agent_mode.get_workflow") as get_workflow:
        response = client.get("/multi-agent/workflow/not-a-uuid")

    assert response.status_code == 400
    get_workflow.assert_not_called()


def test_cannot_decide_another_features_workflow(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    other = {"workflow_id": WORKFLOW_ID, "feature": "student1"}
    with patch("routes.multi_agent_mode.get_workflow", return_value=(other, 200)), \
            patch("routes.multi_agent_mode.record_decision") as record:
        response = client.post(f"/multi-agent/workflow/{WORKFLOW_ID}/decision", json={"decision": "Accept"})

    assert response.status_code == 404
    record.assert_not_called()


def test_decision_forwards_only_decision_fields(client, monkeypatch):
    monkeypatch.setenv("MULTI_AGENT_ENABLED", "true")
    own = {"workflow_id": WORKFLOW_ID, "feature": "student3"}
    with patch("routes.multi_agent_mode.get_workflow", return_value=(own, 200)), \
            patch("routes.multi_agent_mode.record_decision", return_value=({"status": "accepted"}, 200)) as record:
        response = client.post(
            f"/multi-agent/workflow/{WORKFLOW_ID}/decision",
            json={"decision": "Accept", "reviewer": "Tristan", "feature": "student1", "extra": "x"},
        )

    assert response.status_code == 200
    record.assert_called_once_with(WORKFLOW_ID, {"decision": "Accept", "reviewer": "Tristan"})
