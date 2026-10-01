import os
from functools import wraps

from flask import Blueprint, request

from services.mcp_client import mcp_invoke
from views.mcp_formatters import format_mcp_result

mcp_bp = Blueprint("mcp_mode", __name__)


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
    return f'<div class="mcp-result">{format_mcp_result(title, response.get("data"))}</div>', 200


@mcp_bp.post("/mcp/staff-count")
@require_mcp_mode
def mcp_staff_count():
    status = request.form.get("status", "").strip() or None
    department = request.form.get("department", "").strip() or None
    return _render_invoke("Staff Count", "student3_staff_count", {"status": status, "department": department})


@mcp_bp.post("/mcp/staff-by-status")
@require_mcp_mode
def mcp_staff_by_status():
    status = request.form.get("status", "").strip()
    if not status:
        return "<p>Missing required field: status.</p>", 400
    return _render_invoke(f"Staff with status {status}", "student3_staff_by_status", {"status": status})


@mcp_bp.post("/mcp/staff-workload-detail")
@require_mcp_mode
def mcp_staff_workload_detail():
    staff_id_raw = request.form.get("staff_id", "").strip()
    if not staff_id_raw:
        return "<p>Missing required field: staff_id.</p>", 400
    try:
        staff_id = int(staff_id_raw)
    except ValueError:
        return "<p>staff_id must be an integer.</p>", 400
    return _render_invoke(
        f"Workload Detail for Staff #{staff_id}", "student3_staff_workload_detail", {"staff_id": staff_id}
    )


@mcp_bp.post("/mcp/open-alerts")
@require_mcp_mode
def mcp_open_alerts():
    department = request.form.get("department", "").strip() or None
    title = f"Open Alerts in {department}" if department else "Open Alerts"
    return _render_invoke(title, "student3_open_alerts", {"department": department})
