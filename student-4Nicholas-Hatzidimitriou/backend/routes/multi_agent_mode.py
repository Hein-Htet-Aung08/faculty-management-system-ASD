import os
from functools import wraps

import requests
from flask import Blueprint, jsonify, request

MULTI_AGENT_SERVER_URL = os.environ.get("MULTI_AGENT_SERVER_URL", "http://host.docker.internal:5202")

multi_agent_bp = Blueprint("multi_agent_mode", __name__)


def _multi_agent_mode_active():
    return os.environ.get("MULTI_AGENT_ENABLED", "false").lower() == "true"


def require_multi_agent_mode(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _multi_agent_mode_active():
            return jsonify({"error": "Multi-agent mode is off. The server needs MULTI_AGENT_ENABLED set."}), 403
        return fn(*args, **kwargs)

    return wrapper


@multi_agent_bp.route("/api/multi-agent/workflow", methods=["POST"])
@require_multi_agent_mode
def run():
    body = request.get_json(force=True)
    user_request = body.get("user_request", "")
    if not user_request:
        return jsonify({"error": "user_request is required"}), 400

    try:
        resp = requests.post(
            f"{MULTI_AGENT_SERVER_URL}/workflow",
            json={"user_request": user_request, "feature": "student4"},
            timeout=300,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return jsonify({"error": f"Multi-agent server unavailable: {exc}"}), 503


@multi_agent_bp.route("/api/multi-agent/workflow/<workflow_id>/decision", methods=["POST"])
@require_multi_agent_mode
def decision(workflow_id):
    body = request.get_json(force=True)

    try:
        resp = requests.post(
            f"{MULTI_AGENT_SERVER_URL}/workflow/{workflow_id}/decision",
            json=body,
            timeout=30,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return jsonify({"error": f"Multi-agent server unavailable: {exc}"}), 503


@multi_agent_bp.route("/api/multi-agent/workflow/history", methods=["GET"])
@require_multi_agent_mode
def history():
    try:
        resp = requests.get(
            f"{MULTI_AGENT_SERVER_URL}/workflow/history",
            params={"feature": "student4", "limit": request.args.get("limit", 20)},
            timeout=15,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return jsonify({"error": f"Multi-agent server unavailable: {exc}"}), 503
