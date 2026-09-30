"""Student 1 code inside the shared servers: MCP tools (ai-services/mcp-server/tools.py)
and the RAG context loader (ai-services/rag-server/rag_pipeline.py). The Staff
Management API is faked, so neither server nor backend needs to be running."""

import pytest
import requests

STAFF_API = {
    "/api/staff": [
        {"staff_id": 1, "name": "John Smith"},
        {"staff_id": 1, "name": "John Smith"},  # second expertise row -> duplicate id
        {"staff_id": 5, "name": "David Kim"},
    ],
    "/api/staff/1": {
        "staff_id": 1, "name": "John Smith", "email": "john@uni.edu", "phone": "0412",
        "department_name": "Computer Science", "position": "Senior Lecturer",
        "employment_type": "Full-time", "status": "Active",
    },
    "/api/staff/1/expertise": [{"expertise_area": "Machine Learning", "skill_level": 5}],
    "/api/staff/1/qualifications": [
        {"qualification_name": "PhD in Computer Science", "institution": "University of Sydney", "year_obtained": 2015},
    ],
    "/api/staff/1/availability": [{"day": "Monday", "time_slot": "09:00-11:00", "availability_status": "Available"}],
    "/api/staff/5": {
        "staff_id": 5, "name": "David Kim", "email": "david@uni.edu", "phone": "0413",
        "department_name": "Mechanical Engineering", "position": "Professor",
        "employment_type": "Full-time", "status": "On Leave",
    },
    "/api/staff/5/expertise": [{"expertise_area": "Robotics", "skill_level": 5}],
    "/api/staff/5/qualifications": [],
    "/api/staff/5/availability": [],
}


# ---------- MCP tools ----------

@pytest.fixture
def tools(monkeypatch):
    import tools as tools_module

    def fake_call(method, base_url, path, *, params=None, json_body=None):
        if path == "/api/staff/search":
            matches = [{"name": "Grace Tan", "expertise_area": "Cloud Computing"}] if params["expertise"] == "cloud" else []
            return {"status": "success", "data": matches}
        if path in STAFF_API:
            return {"status": "success", "data": STAFF_API[path]}
        return {"status": "error", "http_status": 404, "data": {"error": "Staff member not found"}}

    monkeypatch.setattr(tools_module, "call_feature_api", fake_call)
    return tools_module


def test_get_staff_profile_combines_all_sections(tools):
    result = tools.student1_get_staff_profile(1)

    assert result["status"] == "success"
    assert result["tool"] == "student1_get_staff_profile"
    assert result["data"]["staff"]["name"] == "John Smith"
    assert result["data"]["expertise"][0]["expertise_area"] == "Machine Learning"
    assert result["data"]["qualifications"][0]["institution"] == "University of Sydney"
    assert result["data"]["availability"][0]["day"] == "Monday"


def test_get_staff_profile_passes_through_not_found(tools):
    result = tools.student1_get_staff_profile(999)

    assert result["status"] == "error"
    assert result["http_status"] == 404


@pytest.mark.parametrize("bad_id", [0, -1, "3", 2.5, True, None])
def test_get_staff_profile_rejects_invalid_id(tools, bad_id):
    assert tools.student1_get_staff_profile(bad_id)["error"] == "invalid_input"


def test_search_by_expertise_returns_matches_and_count(tools):
    result = tools.student1_search_staff_by_expertise("  cloud ")

    assert result["status"] == "success"
    assert result["query"] == "cloud"
    assert result["match_count"] == 1
    assert result["data"][0]["name"] == "Grace Tan"


@pytest.mark.parametrize("bad_query", ["", "   ", None, 42])
def test_search_by_expertise_rejects_empty_input(tools, bad_query):
    assert tools.student1_search_staff_by_expertise(bad_query)["error"] == "invalid_input"


def test_tools_are_registered_on_shared_mcp_server():
    pytest.importorskip("mcp")
    import server

    assert "student1_get_staff_profile" in server.AVAILABLE_TOOLS
    assert "student1_search_staff_by_expertise" in server.AVAILABLE_TOOLS


# ---------- RAG context loader ----------

@pytest.fixture
def rag_pipeline(monkeypatch):
    pytest.importorskip("chromadb")
    import rag_pipeline as pipeline

    def fake_call(method, base_url, path, *, params=None):
        return STAFF_API[path]

    monkeypatch.setattr(pipeline, "call_feature_api", fake_call)
    return pipeline


def test_loader_builds_profile_availability_roster_and_summary_chunks(rag_pipeline):
    chunks = rag_pipeline.load_student1_context()
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}

    # 2 unique staff (duplicate /api/staff row ignored): 2 profiles + 2 availability
    # + 2 department rosters + 1 summary
    assert len(chunks) == 7
    assert set(by_id) == {
        "student1_staff_1", "student1_staff_5",
        "student1_availability_1", "student1_availability_5",
        "student1_department_computer_science", "student1_department_mechanical_engineering",
        "student1_summary_counts",
    }

    for chunk in chunks:
        assert chunk["student"] == 1
        assert chunk["feature"] == "staff_management"
        assert chunk["authority_tier"] == "tier_1"
        assert chunk["source_id"].startswith("student1/")

    profile = by_id["student1_staff_1"]["text"]
    assert "Machine Learning (skill level 5/5)" in profile
    assert "PhD in Computer Science" in profile

    assert "none recorded" in by_id["student1_staff_5"]["text"]
    assert "no availability recorded" in by_id["student1_availability_5"]["text"]
    assert "1 Active, 1 On Leave" in by_id["student1_summary_counts"]["text"]


def test_loader_excludes_contact_details(rag_pipeline):
    text = " ".join(chunk["text"] for chunk in rag_pipeline.load_student1_context())

    assert "john@uni.edu" not in text
    assert "0412" not in text


def test_loader_returns_nothing_when_backend_unreachable(rag_pipeline, monkeypatch):
    def unreachable(*args, **kwargs):
        raise requests.ConnectionError("backend down")

    monkeypatch.setattr(rag_pipeline, "call_feature_api", unreachable)

    assert rag_pipeline.load_student1_context() == []
