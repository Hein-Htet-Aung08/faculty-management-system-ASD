import json

from views.html_formatters import _esc, _table, message


def format_mcp_result(title, payload):
    """Render an MCP tool's returned data the same way the rest of the
    dashboard renders rows - a ledger table or a field/value table - instead
    of a raw JSON dump, so MCP Mode matches the team's shared UI.
    """
    heading = f"<h3>{_esc(title)}</h3>"

    if isinstance(payload, list):
        if not payload:
            return heading + message("No records.")
        if not all(isinstance(row, dict) for row in payload):
            return heading + _raw_json(payload)

        columns = []
        for row in payload:
            for key in row:
                if key not in columns:
                    columns.append(key)

        rows = [tuple(row.get(column, "") for column in columns) for row in payload]
        headers = [column.replace("_", " ").title() for column in columns]
        return heading + _table(headers, rows)

    if isinstance(payload, dict):
        if not payload:
            return heading + message("No data returned.")
        rows = [(key.replace("_", " ").title(), value) for key, value in payload.items()]
        return heading + _table(["Field", "Value"], rows)

    return heading + _raw_json(payload)


def _raw_json(payload):
    return f"<pre>{_esc(json.dumps(payload, indent=2, default=str))}</pre>"
