from app import app


def test_htmx_ai_routes_include_hyphenated_aliases():
    rules = {str(rule) for rule in app.url_map.iter_rules()}

    assert "/htmx/projects/<int:project_id>/generate-summary" in rules
    assert "/htmx/projects/<int:project_id>/match-staff" in rules
