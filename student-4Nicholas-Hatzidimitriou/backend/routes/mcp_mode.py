import json
import os
import sys
from functools import wraps

from flask import Blueprint, request

_MCP_SERVER_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mcp-server")
)
if _MCP_SERVER_DIR not in sys.path:
    sys.path.insert(0, _MCP_SERVER_DIR)

from tools import (
    get_project_count,
    get_project_grants_summary,
    get_research_history_for_department,
    search_projects_by_department,
)

mcp_bp = Blueprint("mcp_mode", __name__)


def mcp_render_json(title, payload):
    pretty = json.dumps(payload, indent=2, default=str)
    return f'<div class="mcp-result"><h3>{title}</h3><pre>{pretty}</pre></div>'


def _mcp_mode_active():
    if os.environ.get("MCP_ENABLED", "false").lower() != "true":
        return False
    return request.headers.get("X-MCP-Mode", "").lower() == "on"


def require_mcp_mode(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _mcp_mode_active():
            return (
                "<p>MCP mode is off. The server needs MCP_ENABLED set and the "
                "MCP Tools toggle needs to be on.</p>",
                403,
            )
        return fn(*args, **kwargs)

    return wrapper


@mcp_bp.post("/mcp/project-count")
@require_mcp_mode
def mcp_project_count():
    try:
        count = get_project_count()
        return mcp_render_json("Project Count", {"count": count}), 200
    except Exception as exc:
        return f"<p>MCP tool failed: {exc}</p>", 503


@mcp_bp.post("/mcp/projects-by-department")
@require_mcp_mode
def mcp_projects_by_department():
    department = request.form.get("department", "").strip()
    if not department:
        return "<p>Missing required field: department.</p>", 400
    try:
        projects = search_projects_by_department(department)
        return mcp_render_json(f"Projects in {department}", projects), 200
    except Exception as exc:
        return f"<p>MCP tool failed: {exc}</p>", 503


@mcp_bp.post("/mcp/project-grants-summary")
@require_mcp_mode
def mcp_project_grants_summary():
    project_id_raw = request.form.get("project_id", "").strip()
    if not project_id_raw:
        return "<p>Missing required field: project_id.</p>", 400
    try:
        project_id = int(project_id_raw)
    except ValueError:
        return "<p>project_id must be an integer.</p>", 400

    try:
        summary = get_project_grants_summary(project_id)
        return mcp_render_json(f"Grants Summary for Project #{project_id}", summary), 200
    except ValueError as exc:
        return f"<p>{exc}</p>", 404
    except Exception as exc:
        return f"<p>MCP tool failed: {exc}</p>", 503


@mcp_bp.post("/mcp/research-history")
@require_mcp_mode
def mcp_research_history():
    department = request.form.get("department", "").strip()
    if not department:
        return "<p>Missing required field: department.</p>", 400
    try:
        history = get_research_history_for_department(department)
        return mcp_render_json(f"Research History for {department}", history), 200
    except Exception as exc:
        return f"<p>MCP tool failed: {exc}</p>", 503
