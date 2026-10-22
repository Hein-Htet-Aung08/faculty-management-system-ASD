from unittest.mock import patch

import requests

PROFILES = [
    {"profile_id": 1, "staff_id": 1, "staff_name": "John Smith", "department": "Computer Science", "status": "overloaded"},
    {"profile_id": 3, "staff_id": 3, "staff_name": "Marcus Chen", "department": "Information Technology", "status": "underloaded"},
]
ALERTS = [
    {"alert_id": 1, "staff_id": 1, "alert_type": "overload", "severity": "high", "status": "open"},
]


def fake_db(rows):
    return patch("routes.staff_workload_api.db.list_rows", return_value=rows)


# ------------------------------------------------- endpoint 1: profiles ---

def test_profiles_returns_rows_as_json(client):
    with fake_db(PROFILES) as list_rows:
        response = client.get("/api/staff-workload/profiles")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == PROFILES
    list_rows.assert_called_once_with("staff_workload_profile", status=None, department=None)


def test_profiles_passes_status_and_department_filters(client):
    with fake_db(PROFILES[:1]) as list_rows:
        response = client.get("/api/staff-workload/profiles?status=overloaded&department=Computer%20Science")

    assert response.status_code == 200
    list_rows.assert_called_once_with("staff_workload_profile", status="overloaded", department="Computer Science")


def test_profiles_returns_empty_list_when_nothing_matches(client):
    with fake_db([]):
        response = client.get("/api/staff-workload/profiles?status=overloaded")

    assert response.status_code == 200
    assert response.get_json() == []


def test_profiles_returns_503_when_database_is_unreachable(client):
    with patch("routes.staff_workload_api.db.list_rows", side_effect=requests.ConnectionError("refused")):
        response = client.get("/api/staff-workload/profiles")

    assert response.status_code == 503
    assert "database-service unreachable" in response.get_json()["error"]


# --------------------------------------------------- endpoint 2: alerts ---

def test_alerts_default_to_open_alerts(client):
    with fake_db(ALERTS) as list_rows:
        response = client.get("/api/staff-workload/alerts")

    assert response.status_code == 200
    assert response.get_json() == ALERTS
    list_rows.assert_called_once_with("workload_alert", status="open")


def test_alerts_accept_an_explicit_status(client):
    with fake_db([]) as list_rows:
        response = client.get("/api/staff-workload/alerts?status=resolved")

    assert response.status_code == 200
    list_rows.assert_called_once_with("workload_alert", status="resolved")


def test_alerts_return_503_when_database_times_out(client):
    with patch("routes.staff_workload_api.db.list_rows", side_effect=requests.Timeout("slow")):
        response = client.get("/api/staff-workload/alerts")

    assert response.status_code == 503
    assert "database-service unreachable" in response.get_json()["error"]
