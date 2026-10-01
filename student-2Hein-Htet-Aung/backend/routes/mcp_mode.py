import json
import os

from functools import wraps

from flask import (
    Blueprint,
    request,
)

from services.mcp_client import (
    mcp_invoke,
)


mcp_bp = Blueprint(
    "mcp_mode",
    __name__,
)


def mcp_render_json(
    title,
    payload,
):
    pretty = json.dumps(
        payload,
        indent=2,
        default=str,
    )

    return (
        '<div class="mcp-result">'
        f"<h3>{title}</h3>"
        f"<pre>{pretty}</pre>"
        "</div>"
    )


def _mcp_mode_active():
    if (
        os.environ.get(
            "MCP_ENABLED",
            "false",
        ).lower()
        != "true"
    ):
        return False

    return (
        request.headers.get(
            "X-MCP-Mode",
            "",
        ).lower()
        == "on"
    )


def require_mcp_mode(
    function,
):
    @wraps(function)
    def wrapper(
        *args,
        **kwargs,
    ):
        if not _mcp_mode_active():
            return (
                "<p>"
                "MCP mode is off. "
                "The server needs MCP_ENABLED set and "
                "the MCP Tools toggle needs to be on."
                "</p>",
                403,
            )

        return function(
            *args,
            **kwargs,
        )

    return wrapper


def _render_invoke(
    title,
    tool_name,
    args,
):
    response = mcp_invoke(
        tool_name,
        args,
    )

    if (
        response.get(
            "status"
        )
        == "error"
    ):
        status = (
            response.get(
                "http_status"
            )
            or response.get(
                "_mcp_http_status"
            )
            or 503
        )

        data = response.get(
            "data"
        )

        message = (
            response.get(
                "error"
            )
            or (
                data or {}
            ).get(
                "error"
            )
            or "unknown error"
        )

        return (
            "<p>"
            f"MCP tool failed: {message}"
            "</p>",
            status,
        )

    return (
        mcp_render_json(
            title,
            response.get(
                "data"
            ),
        ),
        200,
    )


@mcp_bp.post(
    "/mcp/check-classroom-availability"
)
@require_mcp_mode
def mcp_check_classroom_availability():
    classroom_id = (
        request.form.get(
            "classroom_id",
            "",
        )
        .strip()
        .upper()
    )

    date = (
        request.form.get(
            "date",
            "",
        )
        .strip()
    )

    year_raw = (
        request.form.get(
            "year",
            "",
        )
        .strip()
    )

    start_time = (
        request.form.get(
            "start_time",
            "",
        )
        .strip()
    )

    end_time = (
        request.form.get(
            "end_time",
            "",
        )
        .strip()
    )

    if not classroom_id:
        return (
            "<p>"
            "Missing required field: classroom_id."
            "</p>",
            400,
        )

    if not date:
        return (
            "<p>"
            "Missing required field: date."
            "</p>",
            400,
        )

    try:
        year = int(
            year_raw
        )

    except ValueError:
        return (
            "<p>"
            "year must be an integer."
            "</p>",
            400,
        )

    if not start_time:
        return (
            "<p>"
            "Missing required field: start_time."
            "</p>",
            400,
        )

    if not end_time:
        return (
            "<p>"
            "Missing required field: end_time."
            "</p>",
            400,
        )

    return _render_invoke(
        (
            "Classroom Availability: "
            f"{classroom_id}"
        ),
        "student2_check_classroom_availability",
        {
            "classroom_id":
                classroom_id,
            "date":
                date,
            "year":
                year,
            "start_time":
                start_time,
            "end_time":
                end_time,
        },
    )


@mcp_bp.post(
    "/mcp/validate-teaching-allocation"
)
@require_mcp_mode
def mcp_validate_teaching_allocation():
    offer_id = (
        request.form.get(
            "offer_id",
            "",
        )
        .strip()
        .upper()
    )

    classroom_id = (
        request.form.get(
            "classroom_id",
            "",
        )
        .strip()
        .upper()
    )

    day = (
        request.form.get(
            "day",
            "",
        )
        .strip()
        .upper()
    )

    date_range = (
        request.form.get(
            "date_range",
            "",
        )
        .strip()
    )

    start_time = (
        request.form.get(
            "start_time",
            "",
        )
        .strip()
    )

    end_time = (
        request.form.get(
            "end_time",
            "",
        )
        .strip()
    )

    class_type = (
        request.form.get(
            "class_type",
            "",
        )
        .strip()
        .upper()
    )

    expected_class_size_raw = (
        request.form.get(
            "expected_class_size",
            "",
        )
        .strip()
    )

    assigned_staff_raw = (
        request.form.get(
            "assigned_staff_member",
            "",
        )
        .strip()
    )

    allocation_status = (
        request.form.get(
            "allocation_status",
            "",
        )
        .strip()
        .upper()
    )

    required_fields = {
        "offer_id":
            offer_id,
        "classroom_id":
            classroom_id,
        "day":
            day,
        "date_range":
            date_range,
        "start_time":
            start_time,
        "end_time":
            end_time,
        "class_type":
            class_type,
        "expected_class_size":
            expected_class_size_raw,
    }

    for (
        field_name,
        value,
    ) in required_fields.items():
        if not value:
            return (
                "<p>"
                "Missing required field: "
                f"{field_name}."
                "</p>",
                400,
            )

    try:
        expected_class_size = int(
            expected_class_size_raw
        )

    except ValueError:
        return (
            "<p>"
            "expected_class_size must be an integer."
            "</p>",
            400,
        )

    assigned_staff_member = None

    if assigned_staff_raw:
        try:
            assigned_staff_member = int(
                assigned_staff_raw
            )

        except ValueError:
            return (
                "<p>"
                "assigned_staff_member must be an integer."
                "</p>",
                400,
            )

    args = {
        "offer_id":
            offer_id,
        "classroom_id":
            classroom_id,
        "day":
            day,
        "date_range":
            date_range,
        "start_time":
            start_time,
        "end_time":
            end_time,
        "class_type":
            class_type,
        "expected_class_size":
            expected_class_size,
        "assigned_staff_member":
            assigned_staff_member,
    }

    if allocation_status:
        args[
            "allocation_status"
        ] = allocation_status

    return _render_invoke(
        "Teaching Allocation Validation",
        "student2_validate_teaching_allocation",
        args,
    )