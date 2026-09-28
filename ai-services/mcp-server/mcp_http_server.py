import importlib
import sys
from pathlib import Path

from flask import Flask, request, jsonify

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ============================================================
# Each student adds their own module below, in the order
# student 1 -> 5. Missing/failed modules are skipped (logged,
# not crashed) by _build_tool_registry(), so this list is safe
# to keep fully "live" - no need to comment a slot out while
# that student's tools.py doesn't exist yet.
# ============================================================
_STUDENT_MODULES = [
    "student_1_andy.tools",     # Student 1: Andy Lam (Staff Management)
    "student_2_hein.tools",     # Student 2: Hein Htet Aung (Teaching, Subject & Classroom Allocation)
    "student_3_tristan.tools",  # Student 3: Tristan Lim (Workload & Availability Management)
    "student_4_nicholas.tools", # Student 4: Nicholas Hatzidimitriou (Research & Grant Management)
    "student_5_matthew.tools",  # Student 5: Matthew Barnard (Performance & Professional Development)
]


def _build_tool_registry():
    registry = {}
    for module_name in _STUDENT_MODULES:
        try:
            module = importlib.import_module(module_name)
            registry.update(module.TOOL_REGISTRY)
        except Exception as exc:
            print(f"[mcp_http_server] {module_name} unavailable or failed: {exc}")
    return registry


TOOL_REGISTRY = _build_tool_registry()

app = Flask(__name__)


@app.route("/invoke", methods=["POST"])
def invoke():
    body = request.get_json(force=True)
    tool_name = body.get("tool")
    args = body.get("args", {})

    if tool_name not in TOOL_REGISTRY:
        return jsonify({"error": f"Unknown tool: {tool_name}", "available_tools": list(TOOL_REGISTRY.keys())}), 404

    try:
        result = TOOL_REGISTRY[tool_name](**args)
        return jsonify({"tool": tool_name, "result": result})
    except ValueError as e:
        return jsonify({"tool": tool_name, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"tool": tool_name, "error": str(e)}), 500


@app.route("/tools", methods=["GET"])
def list_tools():
    return jsonify({"tools": list(TOOL_REGISTRY.keys())})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
