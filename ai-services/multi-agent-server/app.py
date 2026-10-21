import os

from flask import Flask, jsonify, request

from agents.llm_client import OLLAMA_BASE_URL, PLANNER_MODEL, REVIEW_MODEL, WORKER_MODEL
from coordinator import (
    ALLOWED_DECISIONS,
    DecisionConflict,
    WorkflowNotFound,
    get_workflow,
    list_workflows,
    record_decision,
    run_workflow,
    workflow_status,
)
from evidence import describe_features


app = Flask(__name__)


def _error(status_code, message):
    return jsonify({"status": "error", "error": message}), status_code


@app.get("/")
@app.get("/health")
def health():
    return jsonify({
        "service": "multi-agent-server",
        "status": "running",
        "ollama_base_url": OLLAMA_BASE_URL,
        "models": {
            "planner_agent": PLANNER_MODEL,
            "worker_agent": WORKER_MODEL,
            "reviewer_agent": REVIEW_MODEL,
        },
        "features": list(describe_features()),
        "human_decisions": ALLOWED_DECISIONS,
    })


@app.get("/features")
def features():
    return jsonify({"status": "success", "features": describe_features()})


@app.post("/workflow")
def workflow():
    data = request.get_json(silent=True) or {}
    try:
        result = run_workflow(data.get("user_request"), data.get("feature"))
    except ValueError as exc:
        return _error(400, str(exc))
    return jsonify(result), 200


@app.get("/workflow/status")
def status():
    return jsonify(workflow_status()), 200


@app.get("/workflow/history")
def history():
    try:
        limit = max(1, min(int(request.args.get("limit", "20")), 100))
    except ValueError:
        return _error(400, "limit must be a number")
    return jsonify({
        "status": "success",
        "workflows": list_workflows(request.args.get("feature"), limit),
    })


@app.get("/workflow/<workflow_id>")
def workflow_detail(workflow_id):
    try:
        return jsonify(get_workflow(workflow_id))
    except WorkflowNotFound:
        return _error(404, f"workflow {workflow_id} not found")


@app.post("/workflow/<workflow_id>/decision")
def decision(workflow_id):
    data = request.get_json(silent=True) or {}
    try:
        result = record_decision(
            workflow_id,
            data.get("decision"),
            reviewer=data.get("reviewer"),
            notes=data.get("notes"),
            correction=data.get("correction"),
        )
    except WorkflowNotFound:
        return _error(404, f"workflow {workflow_id} not found")
    except DecisionConflict as exc:
        return _error(409, str(exc))
    except ValueError as exc:
        return _error(400, str(exc))
    return jsonify(result), 200


def main():
    # Bound to all interfaces so Docker backends can reach it through
    # host.docker.internal, like the shared MCP and RAG servers.
    host = os.getenv("MULTI_AGENT_HOST", "0.0.0.0")  # noqa: S104
    # 5004 is the Student 4 backend; MCP is 5201 and RAG is 5200.
    port = int(os.getenv("MULTI_AGENT_PORT", "5202"))
    print(f"multi-agent-server listening on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
