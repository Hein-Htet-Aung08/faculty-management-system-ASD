"""Release 2 post-commit CI endpoint tests for Student 1 (Staff Management).

The two endpoint functions under test:
  1. GET  /api/staff/<staff_id>  -- get_staff_by_id
  2. POST /api/staff             -- create_staff

Each test runs against a fresh copy of the database built by the real
init_db.py and seed.py scripts (see conftest.py), so no test depends on
another. Saved output: reports/release2/endpoint-tests.txt.
"""

NEW_STAFF = {
    "name": "Release Two Tester",
    "email": "release.two@university.edu",
    "phone": "0400000002",
    "department_id": 1,
    "position": "Lecturer",
    "employment_type": "Full-time",
    "status": "Active",
    "expertise_area": "Continuous Integration",
    "skill_level": 4,
}


# ---------- Endpoint 1: GET /api/staff/<staff_id> ----------

def test_get_staff_returns_seeded_record(client):
    response = client.get("/api/staff/1")

    assert response.status_code == 200
    assert response.json["staff_id"] == 1
    assert response.json["name"] == "John Smith"


def test_get_staff_joins_department_name(client):
    response = client.get("/api/staff/1")

    assert response.json["department_name"] == "Computer Science"
    assert response.json["department_id"] == 1


def test_get_staff_returns_all_profile_fields(client):
    response = client.get("/api/staff/2")

    expected_fields = {
        "staff_id", "name", "email", "phone", "department_id",
        "department_name", "position", "employment_type", "status",
    }
    assert expected_fields <= set(response.json)


def test_get_staff_unknown_id_returns_404(client):
    response = client.get("/api/staff/9999")

    assert response.status_code == 404
    assert response.json["error"] == "Staff member not found"


# ---------- Endpoint 2: POST /api/staff ----------

def test_create_staff_returns_201_with_new_id(client):
    response = client.post("/api/staff", json=NEW_STAFF)

    assert response.status_code == 201
    assert response.json["message"] == "Staff member created"
    assert isinstance(response.json["staff_id"], int)


def test_created_staff_is_returned_by_get_endpoint(client):
    staff_id = client.post("/api/staff", json=NEW_STAFF).json["staff_id"]

    response = client.get(f"/api/staff/{staff_id}")

    assert response.status_code == 200
    assert response.json["name"] == NEW_STAFF["name"]
    assert response.json["department_name"] == "Computer Science"


def test_create_staff_stores_initial_expertise(client):
    staff_id = client.post("/api/staff", json=NEW_STAFF).json["staff_id"]

    response = client.get(f"/api/staff/{staff_id}/expertise")

    assert response.json == [{
        "expertise_id": response.json[0]["expertise_id"],
        "expertise_area": "Continuous Integration",
        "skill_level": 4,
    }]


def test_create_staff_missing_field_returns_400(client):
    incomplete = {key: value for key, value in NEW_STAFF.items() if key != "email"}

    response = client.post("/api/staff", json=incomplete)

    assert response.status_code == 400
    assert "email" in response.json["error"]


def test_create_staff_unknown_department_returns_400(client):
    response = client.post("/api/staff", json={**NEW_STAFF, "department_id": 9999})

    assert response.status_code == 400
    assert "Invalid data" in response.json["error"]


def test_failed_create_does_not_add_staff(client):
    before = len({row["staff_id"] for row in client.get("/api/staff").json})

    client.post("/api/staff", json={**NEW_STAFF, "department_id": 9999})

    after = len({row["staff_id"] for row in client.get("/api/staff").json})
    assert after == before
