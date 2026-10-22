import os
from urllib.parse import quote

import requests


def enabled():
    return os.getenv("MULTI_AGENT_ENABLED", "false").lower() == "true"


def call_server(method, path, payload=None, params=None, timeout=20):
    base_url = os.getenv("MULTI_AGENT_SERVER_URL", "http://127.0.0.1:5202").rstrip("/")
    try:
        response = requests.request(
            method, f"{base_url}/{path}", json=payload, params=params, timeout=timeout
        )
    except requests.RequestException:
        return {"error": "Multi-Agent server is unavailable"}, 503
    try:
        result = response.json()
    except ValueError:
        return {"error": "Multi-Agent server returned an invalid response"}, 502
    if not isinstance(result, dict):
        return {"error": "Multi-Agent server returned an invalid response"}, 502
    return result, response.status_code


def start_workflow(user_request):
    return call_server(
        "POST", "workflow",
        payload={"user_request": user_request, "feature": "student5"}, timeout=420,
    )


def workflow_history(limit):
    result, status = call_server(
        "GET", "workflow/history", params={"feature": "student5", "limit": limit}
    )
    if status == 200:
        workflows = result.get("workflows")
        if not isinstance(workflows, list) or any(not isinstance(row, dict) for row in workflows):
            return {"error": "Multi-Agent server returned an invalid response"}, 502
        result["workflows"] = [row for row in workflows if row.get("feature") == "student5"]
    return result, status


def get_workflow(workflow_id):
    result, status = call_server("GET", f"workflow/{quote(workflow_id, safe='')}")
    if status == 200 and result.get("feature") != "student5":
        return {"error": "Workflow not found"}, 404
    return result, status


def submit_decision(workflow_id, payload):
    result, status = get_workflow(workflow_id)
    if status != 200:
        return result, status
    return call_server(
        "POST", f"workflow/{quote(workflow_id, safe='')}/decision", payload=payload
    )
