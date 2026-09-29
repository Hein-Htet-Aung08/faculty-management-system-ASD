import json
import os
from functools import wraps

from flask import Blueprint, request

from services.mcp_client import mcp_invoke

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


def _render_invoke(title, tool_name, args):
    response = mcp_invoke(tool_name, args)
    if response.get("status") == "error":
        status = response.get("http_status") or response.get("_mcp_http_status") or 503
        data = response.get("data")
        message = response.get("error") or (data or {}).get("error") or "unknown error"
        return f"<p>MCP tool failed: {message}</p>", status
    return mcp_render_json(title, response.get("data")), 200


@mcp_bp.post("/mcp/project-count")
@require_mcp_mode
def mcp_project_count():
    return _render_invoke("Project Count", "student4_project_count", {})


@mcp_bp.post("/mcp/projects-by-department")
@require_mcp_mode
def mcp_projects_by_department():
    department = request.form.get("department", "").strip()
    if not department:
        return "<p>Missing required field: department.</p>", 400
    return _render_invoke(
        f"Projects in {department}", "student4_projects_by_department", {"department": department}
    )


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
    return _render_invoke(
        f"Grants Summary for Project #{project_id}",
        "student4_project_grants_summary",
        {"project_id": project_id},
    )


@mcp_bp.post("/mcp/research-history")
@require_mcp_mode
def mcp_research_history():
    department = request.form.get("department", "").strip()
    if not department:
        return "<p>Missing required field: department.</p>", 400
    return _render_invoke(
        f"Research History for {department}", "student4_research_history", {"department": department}
    )
