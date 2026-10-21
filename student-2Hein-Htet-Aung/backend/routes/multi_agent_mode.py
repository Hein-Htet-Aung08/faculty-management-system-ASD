
import os
from functools import wraps

import requests
from flask import Blueprint, jsonify, request


multi_agent_bp = Blueprint("multi_agent_mode", __name__)

MULTI_AGENT_SERVER_URL = os.getenv(
    "MULTI_AGENT_SERVER_URL",
    "http://host.docker.internal:5202",
).rstrip("/")


def require_multi_agent(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        enabled = os.getenv(
            "MULTI_AGENT_ENABLED", "false"
        ).lower() == "true"

        if not enabled:
            return jsonify({
                "error": "Multi-Agent mode is disabled."
            }), 403

        return function(*args, **kwargs)

    return wrapper


def call_server(method, path, timeout=20, **kwargs):
    try:
        response = requests.request(
            method,
            f"{MULTI_AGENT_SERVER_URL}/{path.lstrip('/')}",
            timeout=timeout,
            **kwargs,
        )
    except requests.RequestException:
        return {
            "error": "Multi-Agent server is unavailable."
        }, 503

    try:
        return response.json(), response.status_code
    except ValueError:
        return {
            "error": "Invalid Multi-Agent server response."
        }, 502


def get_owned_workflow(workflow_id):
    result, status = call_server(
        "GET", f"workflow/{workflow_id}"
    )

    if status == 200:
        if (
            not isinstance(result, dict)
            or result.get("feature") != "student2"
        ):
            return {"error": "Workflow not found."}, 404

    return result, status


@multi_agent_bp.post("/multi-agent/workflow")
@require_multi_agent
def run_workflow():
    body = request.get_json(silent=True) or {}
    user_request = body.get("user_request")

    if not isinstance(user_request, str) or not user_request.strip():
        return jsonify({
            "error": "user_request is required."
        }), 400

    result, status = call_server(
        "POST",
        "workflow",
        json={
            "user_request": user_request.strip(),
            "feature": "student2",
        },
        timeout=420,
    )

    return jsonify(result), status


@multi_agent_bp.get("/multi-agent/workflow/history")
@require_multi_agent
def workflow_history():
    result, status = call_server(
        "GET",
        "workflow/history",
        params={
            "feature": "student2",
            "limit": request.args.get("limit", "20"),
        },
    )

    return jsonify(result), status


@multi_agent_bp.get("/multi-agent/workflow/<string:workflow_id>")
@require_multi_agent
def workflow_details(workflow_id):
    result, status = get_owned_workflow(workflow_id)
    return jsonify(result), status


@multi_agent_bp.post("/multi-agent/workflow/<string:workflow_id>/decision")
@require_multi_agent
def submit_human_decision(workflow_id):
    existing, status = get_owned_workflow(workflow_id)

    if status != 200:
        return jsonify(existing), status

    body = request.get_json(silent=True) or {}

    decision_data = {
        key: body[key]
        for key in ("decision", "reviewer", "notes", "correction")
        if key in body
    }

    result, status = call_server(
        "POST",
        f"workflow/{workflow_id}/decision",
        json=decision_data,
    )

    return jsonify(result), status
