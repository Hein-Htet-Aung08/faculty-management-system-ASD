"""Release 1 MCP/RAG routes. The shared servers are never contacted: they are
either disabled (as in CI) or replaced with fakes."""

import pytest

import ai_services_client as ai_services

CLOSED_PORT_URL = "http://127.0.0.1:9"


@pytest.fixture
def mcp_on(monkeypatch):
    monkeypatch.setattr(ai_services, "MCP_ENABLED", True)


@pytest.fixture
def rag_on(monkeypatch):
    monkeypatch.setattr(ai_services, "RAG_ENABLED", True)


# ---------- disabled (CI default) ----------

def test_status_reports_both_disabled_by_default(client):
    response = client.get("/api/ai-services/status")

    assert response.json == {"mcp_enabled": False, "rag_enabled": False}


@pytest.mark.parametrize("path, body", [
    ("/api/mcp/staff-profile", {"staff_id": 1}),
    ("/api/mcp/search-expertise", {"expertise": "cloud"}),
    ("/api/rag/ask", {"question": "Who teaches cloud?"}),
    ("/api/rag/refresh", None),
])
def test_routes_return_503_when_disabled(client, path, body):
    response = client.post(path, json=body)

    assert response.status_code == 503
    assert "disabled" in response.json["error"]


# ---------- MCP ----------

def test_mcp_profile_returns_tool_result(client, mcp_on, monkeypatch):
    calls = []

    def fake_tool(tool_name, arguments):
        calls.append((tool_name, arguments))
        return {"status": "success", "tool": tool_name, "data": {"staff": {"name": "Marcus Chen"}}}

    monkeypatch.setattr(ai_services, "call_mcp_tool", fake_tool)

    response = client.post("/api/mcp/staff-profile", json={"staff_id": "3"})

    assert response.status_code == 200
    assert response.json["data"]["staff"]["name"] == "Marcus Chen"
    assert calls == [("student1_get_staff_profile", {"staff_id": 3})]


def test_mcp_search_passes_trimmed_expertise(client, mcp_on, monkeypatch):
    calls = []
    monkeypatch.setattr(
        ai_services, "call_mcp_tool",
        lambda tool_name, arguments: calls.append((tool_name, arguments)) or {"status": "success", "data": []},
    )

    response = client.post("/api/mcp/search-expertise", json={"expertise": "  cloud  "})

    assert response.status_code == 200
    assert calls == [("student1_search_staff_by_expertise", {"expertise": "cloud"})]


@pytest.mark.parametrize("path, body", [
    ("/api/mcp/staff-profile", {"staff_id": "abc"}),
    ("/api/mcp/staff-profile", {}),
    ("/api/mcp/search-expertise", {"expertise": "   "}),
])
def test_mcp_rejects_bad_input_before_calling_server(client, mcp_on, monkeypatch, path, body):
    monkeypatch.setattr(ai_services, "call_mcp_tool", lambda *args: pytest.fail("server should not be called"))

    assert client.post(path, json=body).status_code == 400


@pytest.mark.parametrize("tool_result, expected_status", [
    ({"status": "error", "http_status": 404, "data": {"error": "Staff member not found"}}, 404),
    ({"status": "error", "error": "invalid_input", "details": "bad"}, 400),
    ({"status": "error", "error": "feature_service_unavailable"}, 502),
])
def test_mcp_tool_errors_map_to_http_status(client, mcp_on, monkeypatch, tool_result, expected_status):
    monkeypatch.setattr(ai_services, "call_mcp_tool", lambda *args: tool_result)

    response = client.post("/api/mcp/staff-profile", json={"staff_id": 1})

    assert response.status_code == expected_status
    assert response.json == tool_result


def test_mcp_unreachable_server_returns_503(client, mcp_on, monkeypatch):
    monkeypatch.setattr(ai_services, "MCP_SERVER_URL", f"{CLOSED_PORT_URL}/mcp")
    monkeypatch.setattr(ai_services, "MCP_TIMEOUT_SECONDS", 5)

    response = client.post("/api/mcp/staff-profile", json={"staff_id": 1})

    assert response.status_code == 503
    assert "Could not reach MCP server" in response.json["error"]


# ---------- RAG ----------

GROUNDED_REPLY = {
    "status": "success",
    "answer": "David Kim has expertise in robotics.",
    "confidence_category": "High",
    "citations": [{"source_id": "student1/staff/5", "feature": "staff_management"}],
}


def test_rag_answer_includes_citations_and_confidence(client, rag_on, monkeypatch):
    sent = []
    monkeypatch.setattr(ai_services, "_post_rag", lambda path, payload: sent.append((path, payload)) or GROUNDED_REPLY)

    response = client.post("/api/rag/ask", json={"question": "Who knows robotics?"})

    assert response.status_code == 200
    assert response.json["answer"] == "David Kim has expertise in robotics."
    assert response.json["confidence_category"] == "High"
    assert response.json["citations"][0]["source_id"] == "student1/staff/5"
    assert response.json["insufficient_context"] is False
    assert sent[0][0] == "answer"
    assert sent[0][1]["query"] == "Who knows robotics?"
    assert sent[0][1]["k"] == ai_services.RAG_TOP_K == 8


@pytest.mark.parametrize("model_answer", ["Insufficient context.", "insufficient context", ""])
def test_rag_model_refusal_is_reported_as_insufficient_context(client, rag_on, monkeypatch, model_answer):
    reply = {**GROUNDED_REPLY, "answer": model_answer}
    monkeypatch.setattr(ai_services, "_post_rag", lambda *args: reply)

    response = client.post("/api/rag/ask", json={"question": "What is the capital of France?"})

    assert response.status_code == 200
    assert response.json["insufficient_context"] is True
    assert response.json["answer"] == "Insufficient context."
    assert response.json["confidence_category"] == "Insufficient"
    assert response.json["citations"] == []


def test_rag_requires_question(client, rag_on):
    assert client.post("/api/rag/ask", json={"question": "  "}).status_code == 400


def test_rag_server_error_returns_503(client, rag_on, monkeypatch):
    monkeypatch.setattr(
        ai_services, "_post_rag",
        lambda *args: {"status": "error", "error": "local_model_unavailable", "details": "Ollama down"},
    )

    response = client.post("/api/rag/ask", json={"question": "Who knows robotics?"})

    assert response.status_code == 503
    assert "Ollama down" in response.json["error"]


def test_rag_unreachable_server_returns_503(client, rag_on, monkeypatch):
    monkeypatch.setattr(ai_services, "RAG_SERVER_URL", CLOSED_PORT_URL)

    response = client.post("/api/rag/ask", json={"question": "Who knows robotics?"})

    assert response.status_code == 503
    assert "Could not reach RAG server" in response.json["error"]


def test_rag_refresh_returns_chunk_count(client, rag_on, monkeypatch):
    monkeypatch.setattr(ai_services, "_post_rag", lambda *args: {"status": "success", "chunk_count": 29})

    response = client.post("/api/rag/refresh")

    assert response.status_code == 200
    assert response.json == {"chunk_count": 29}
