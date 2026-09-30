"""Release 0 Staff Management behaviour must keep working after Release 1."""

import app as app_module

NEW_STAFF = {
    "name": "Test Person",
    "email": "test.person@university.edu",
    "phone": "0400000000",
    "department_id": 1,
    "position": "Lecturer",
    "employment_type": "Full-time",
    "status": "Active",
    "expertise_area": "Test Automation",
    "skill_level": 4,
}


def test_list_staff_returns_seeded_records(client):
    response = client.get("/api/staff")

    assert response.status_code == 200
    assert len(response.json) >= 10


def test_get_staff_by_id(client):
    response = client.get("/api/staff/1")

    assert response.status_code == 200
    assert response.json["name"] == "John Smith"
    assert response.json["department_name"] == "Computer Science"


def test_get_unknown_staff_returns_404(client):
    assert client.get("/api/staff/9999").status_code == 404


def test_create_then_delete_staff(client):
    created = client.post("/api/staff", json=NEW_STAFF)
    assert created.status_code == 201
    staff_id = created.json["staff_id"]

    fetched = client.get(f"/api/staff/{staff_id}")
    assert fetched.json["name"] == "Test Person"
    assert client.get(f"/api/staff/{staff_id}/expertise").json[0]["expertise_area"] == "Test Automation"

    assert client.delete(f"/api/staff/{staff_id}").status_code == 200
    assert client.get(f"/api/staff/{staff_id}").status_code == 404


def test_create_staff_missing_field_returns_400(client):
    incomplete = {key: value for key, value in NEW_STAFF.items() if key != "email"}

    response = client.post("/api/staff", json=incomplete)

    assert response.status_code == 400
    assert "email" in response.json["error"]


def test_update_staff(client):
    updated = {key: value for key, value in NEW_STAFF.items() if key not in ("expertise_area", "skill_level")}
    updated["name"] = "John Smith Updated"

    response = client.put("/api/staff/1", json=updated)

    assert response.status_code == 200
    assert client.get("/api/staff/1").json["name"] == "John Smith Updated"


def test_update_unknown_staff_returns_404(client):
    updated = {key: value for key, value in NEW_STAFF.items() if key not in ("expertise_area", "skill_level")}

    assert client.put("/api/staff/9999", json=updated).status_code == 404


def test_delete_unknown_staff_returns_404(client):
    assert client.delete("/api/staff/9999").status_code == 404


def test_search_by_expertise(client):
    response = client.get("/api/staff/search?expertise=machine")

    assert response.status_code == 200
    assert [row["name"] for row in response.json] == ["John Smith"]


def test_filter_by_department(client):
    response = client.get("/api/staff/filter?department_id=1")

    assert response.status_code == 200
    assert {row["department_name"] for row in response.json} == {"Computer Science"}


def test_list_departments(client):
    response = client.get("/api/departments")

    assert response.status_code == 200
    assert len(response.json) == 10


def test_generate_analysis_uses_llm_summary_and_rule_based_score(client, monkeypatch):
    monkeypatch.setattr(app_module, "generate_response", lambda *args, **kwargs: "Stub summary.")

    response = client.post("/api/staff/1/generate_analysis")

    assert response.status_code == 201
    assert response.json["generated_summary"] == "Stub summary."
    # Deterministic score: skill level 5 * 2
    assert response.json["suitability_score"] == 10.0


def test_generate_analysis_reports_unavailable_llm(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise RuntimeError("Could not connect to Ollama")

    monkeypatch.setattr(app_module, "generate_response", unavailable)

    response = client.post("/api/staff/1/generate_analysis")

    assert response.status_code == 503
    assert "AI service unavailable" in response.json["error"]
