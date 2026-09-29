import re

from flask import Flask, request, jsonify

import tools

# ============================================================
# Common HTTP Wrapper
# ============================================================
#
# Real MCP stdio transport (server.py) is built for one local
# client talking to one locally-spawned process, not five backend
# containers on their own networks all calling into one shared
# server - so backends talk to this plain HTTP wrapper instead.
#
# Every "student{N}_<tool_name>" function on the shared tools
# module is picked up automatically, so adding a new tool to
# tools.py is enough - nothing here needs editing per student.

_TOOL_NAME_RE = re.compile(r"^student\d+_[a-zA-Z0-9_]+$")


def _build_tool_registry():
    registry = {}
    for name in dir(tools):
        if _TOOL_NAME_RE.match(name) and callable(getattr(tools, name)):
            registry[name] = getattr(tools, name)
    return registry


TOOL_REGISTRY = _build_tool_registry()

app = Flask(__name__)


@app.route("/invoke", methods=["POST"])
def invoke():
    body = request.get_json(force=True)
    tool_name = body.get("tool")
    args = body.get("args", {})

    if tool_name not in TOOL_REGISTRY:
        return jsonify({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TOOL_REGISTRY.keys()),
        }), 404

    try:
        return jsonify(TOOL_REGISTRY[tool_name](**args))
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify({"tools": list(TOOL_REGISTRY.keys())})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # RAG's shared HTTP server defaults to 5200 (student 3 already
    # uses 5003), so the shared MCP HTTP wrapper follows the same
    # numbering and defaults to 5201.
    app.run(host="0.0.0.0", port=5201)
