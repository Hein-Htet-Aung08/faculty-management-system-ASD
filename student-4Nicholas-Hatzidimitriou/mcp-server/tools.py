import os

import requests

DATABASE_SERVICE_URL = os.environ.get("DATABASE_SERVICE_URL", "http://localhost:5104")


def _get(path, params=None):
    try:
        response = requests.get(f"{DATABASE_SERVICE_URL}{path}", params=params, timeout=10)
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(f"database-service unreachable at {DATABASE_SERVICE_URL}") from exc
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _clean_params(params):
    return {k: v for k, v in params.items() if v is not None}


def get_project_count(department=None, status=None):
    projects = _get("/projects", _clean_params({"department": department, "status": status})) or []
    return len(projects)


def search_projects_by_department(department: str):
    return _get("/projects", {"department": department}) or []


def get_project_grants_summary(project_id: int):
    project = _get(f"/projects/{project_id}")
    if project is None:
        raise ValueError(f"Project {project_id} does not exist.")

    grants = _get("/grants", {"projectID": project_id}) or []
    total_requested = sum(g["amountRequested"] for g in grants)
    total_awarded = sum(g["amountAwarded"] or 0 for g in grants)

    return {
        "projectID": project_id,
        "title": project["title"],
        "grantCount": len(grants),
        "totalRequested": total_requested,
        "totalAwarded": total_awarded,
        "grants": grants,
    }


def get_research_history_for_department(department: str):
    projects = _get("/projects", {"department": department}) or []
    history = []
    for project in projects:
        analyses = _get("/ai-analysis", {"projectID": project["projectID"]}) or []
        summaries = [a["generatedSummary"] for a in analyses if a.get("generatedSummary")]
        history.append(
            {
                "projectID": project["projectID"],
                "title": project["title"],
                "summaries": summaries,
            }
        )
    return history


if __name__ == "__main__":
    print("get_project_count():")
    print(" ", get_project_count())

    print("search_projects_by_department('Computer Science'):")
    for project in search_projects_by_department("Computer Science"):
        print(" ", project)

    print("get_project_grants_summary(1):")
    try:
        print(" ", get_project_grants_summary(1))
    except Exception as exc:
        print("  failed:", exc)

    print("get_research_history_for_department('Computer Science'):")
    for entry in get_research_history_for_department("Computer Science"):
        print(" ", entry)
