import os

import requests

MULTI_AGENT_SERVER_URL = os.environ.get("MULTI_AGENT_SERVER_URL", "http://host.docker.internal:5202")

# Every request from this backend is for the Student 3 feature, so the
# Worker only ever sees workload evidence.
FEATURE_KEY = "student3"

# A workflow runs three model calls (Planner, Worker, Reviewer); with
# llama3.1:8b loading cold on a CPU-only box that can take minutes.
try:
    WORKFLOW_TIMEOUT = float(os.environ.get("MULTI_AGENT_TIMEOUT", "300"))
except ValueError:
    WORKFLOW_TIMEOUT = 300.0
SHORT_TIMEOUT = 15


def _call(method, path, *, json_body=None, params=None, timeout=SHORT_TIMEOUT):
    """Return (payload, status_code). The server's own 400/404/409 pass through."""
    try:
        resp = requests.request(
            method, f"{MULTI_AGENT_SERVER_URL}{path}", json=json_body, params=params, timeout=timeout
        )
    except requests.RequestException as e:
        return {"status": "error", "error": f"Multi-Agent server unavailable: {e}"}, 503

    try:
        return resp.json(), resp.status_code
    except ValueError:
        return {"status": "error", "error": f"Multi-Agent server returned HTTP {resp.status_code} without JSON"}, 502


def server_health():
    return _call("GET", "/health", timeout=5)


def run_workflow(user_request: str):
    return _call(
        "POST", "/workflow", json_body={"user_request": user_request, "feature": FEATURE_KEY}, timeout=WORKFLOW_TIMEOUT
    )


def get_workflow(workflow_id: str):
    return _call("GET", f"/workflow/{workflow_id}")


def record_decision(workflow_id: str, decision: dict):
    return _call("POST", f"/workflow/{workflow_id}/decision", json_body=decision)


def workflow_history(limit: int):
    return _call("GET", "/workflow/history", params={"feature": FEATURE_KEY, "limit": limit})
