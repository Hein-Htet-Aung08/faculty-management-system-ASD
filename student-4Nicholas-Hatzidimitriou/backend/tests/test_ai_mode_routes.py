import os

from app import app


def test_htmx_ai_routes_include_hyphenated_aliases():
    rules = {str(rule) for rule in app.url_map.iter_rules()}

    assert "/htmx/projects/<int:project_id>/generate-summary" in rules
    assert "/htmx/projects/<int:project_id>/match-staff" in rules


def test_ai_mode_routes_return_403_when_disabled():
    os.environ.pop("AI_MODE_ENABLED", None)
    client = app.test_client()

    response = client.post("/htmx/projects/1/generate-summary")

    assert response.status_code == 403
    assert b"AI-Mode is off" in response.data
