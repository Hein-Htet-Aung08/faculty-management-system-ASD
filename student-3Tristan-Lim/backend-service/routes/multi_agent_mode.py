import os
import uuid
from functools import wraps

from flask import Blueprint, jsonify, request
from services.multi_agent_api import (
    FEATURE_KEY,
    get_workflow,
    record_decision,
    run_workflow,
    server_health,
    workflow_history,
)

multi_agent_bp = Blueprint("multi_agent_mode", __name__)

DECISION_FIELDS = ("decision", "reviewer", "notes", "correction")


def _multi_agent_mode_active():
    return os.environ.get("MULTI_AGENT_ENABLED", "false").lower() == "true"


def require_multi_agent_mode(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _multi_agent_mode_active():
            return jsonify({"error": "Multi-Agent mode is off. The server needs MULTI_AGENT_ENABLED set to true."}), 403
        return fn(*args, **kwargs)

    return wrapper


def _own_workflow(workflow_id):
    """Fetch a workflow only if the id is a UUID and it belongs to Student 3.

    Returns (payload, status_code). Another feature's workflow is reported
    as not found so this tab can never read or decide it.
    """
    try:
        workflow_id = str(uuid.UUID(workflow_id))
    except ValueError:
        return {"error": "workflow id must be a UUID"}, 400

    payload, status = get_workflow(workflow_id)
    if status == 200 and payload.get("feature") != FEATURE_KEY:
        return {"error": f"workflow {workflow_id} not found"}, 404
    return payload, status


@multi_agent_bp.get("/multi-agent/status")
def status():
    # Not gated: the tab uses this to show whether the mode is on.
    body = {"enabled": _multi_agent_mode_active(), "feature": FEATURE_KEY}
    if body["enabled"]:
        health, code = server_health()
        body["server"] = "reachable" if code == 200 else "unreachable"
        if code == 200:
            body["models"] = health.get("models", {})
        else:
            body["error"] = health.get("error")
    return jsonify(body)


@multi_agent_bp.post("/multi-agent/workflow")
@require_multi_agent_mode
def workflow():
    body = request.get_json(silent=True) or {}
    user_request = str(body.get("user_request", "")).strip()
    if not user_request:
        return jsonify({"error": "user_request is required"}), 400
    payload, code = run_workflow(user_request)
    return jsonify(payload), code


@multi_agent_bp.get("/multi-agent/workflow/history")
@require_multi_agent_mode
def history():
    try:
        limit = max(1, min(int(request.args.get("limit", "10")), 50))
    except ValueError:
        return jsonify({"error": "limit must be a number"}), 400
    payload, code = workflow_history(limit)
    return jsonify(payload), code


@multi_agent_bp.get("/multi-agent/workflow/<workflow_id>")
@require_multi_agent_mode
def workflow_detail(workflow_id):
    payload, code = _own_workflow(workflow_id)
    return jsonify(payload), code


@multi_agent_bp.post("/multi-agent/workflow/<workflow_id>/decision")
@require_multi_agent_mode
def decision(workflow_id):
    payload, code = _own_workflow(workflow_id)
    if code != 200:
        return jsonify(payload), code

    body = request.get_json(silent=True) or {}
    decision_body = {field: body.get(field) for field in DECISION_FIELDS if body.get(field) is not None}
    payload, code = record_decision(payload["workflow_id"], decision_body)
    return jsonify(payload), code
