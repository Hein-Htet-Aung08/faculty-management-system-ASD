import os

import pytest
import requests

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:5004")

REQUIRED_PROJECT_FIELDS = {"projectID", "title", "department", "status"}


def test_get_projects_returns_seeded_data():
    response = requests.get(f"{BASE_URL}/projects", timeout=10)
    assert response.status_code == 200

    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) >= 10, f"expected at least 10 seeded projects, got {len(projects)}"

    for project in projects:
        missing = REQUIRED_PROJECT_FIELDS - project.keys()
        assert not missing, f"project {project} is missing fields: {missing}"


def test_get_project_by_id_returns_single_project():
    projects = requests.get(f"{BASE_URL}/projects", timeout=10).json()
    known_id = projects[0]["projectID"]

    response = requests.get(f"{BASE_URL}/projects/{known_id}", timeout=10)
    assert response.status_code == 200

    project = response.json()
    assert project["projectID"] == known_id
    missing = REQUIRED_PROJECT_FIELDS - project.keys()
    assert not missing, f"project {project} is missing fields: {missing}"


def test_get_project_by_unknown_id_returns_404():
    response = requests.get(f"{BASE_URL}/projects/999999", timeout=10)
    assert response.status_code == 404
    assert "error" in response.json()
