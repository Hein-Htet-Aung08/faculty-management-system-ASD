import os

import pytest
import requests

BACKEND = os.environ.get("LIVE_BACKEND_URL")

pytestmark = pytest.mark.skipif(not BACKEND, reason="LIVE_BACKEND_URL not set")


def get(path):
    response = requests.get(f"{BACKEND}{path}", timeout=10)
    return response.status_code, response.json()


def test_live_profiles_returns_all_seeded_staff():
    status, rows = get("/api/staff-workload/profiles")

    assert status == 200
    assert len(rows) == 10
    assert {"staff_id", "staff_name", "department", "current_total_hours", "max_weekly_hours", "status"} <= rows[0].keys()


def test_live_profiles_filters_by_status():
    status, rows = get("/api/staff-workload/profiles?status=overloaded")

    assert status == 200
    assert sorted(r["staff_name"] for r in rows) == ["Hana Suzuki", "John Smith", "Priya Nair"]
    assert all(r["current_total_hours"] > r["max_weekly_hours"] for r in rows)


def test_live_alerts_default_to_open():
    status, rows = get("/api/staff-workload/alerts")

    assert status == 200
    assert len(rows) == 8
    assert {r["status"] for r in rows} == {"open"}


def test_live_alerts_filter_resolved():
    status, rows = get("/api/staff-workload/alerts?status=resolved")

    assert status == 200
    assert [r["alert_id"] for r in rows] == [11]
