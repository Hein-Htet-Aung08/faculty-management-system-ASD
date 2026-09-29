import os

import requests

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://host.docker.internal:5201")


def mcp_invoke(tool_name: str, args: dict) -> dict:
    try:
        resp = requests.post(f"{MCP_SERVER_URL}/invoke", json={"tool": tool_name, "args": args}, timeout=15)
    except requests.RequestException as e:
        return {"status": "error", "error": f"MCP server unavailable: {e}", "_mcp_http_status": 503}

    try:
        body = resp.json()
    except ValueError:
        return {"status": "error", "error": f"MCP server returned a non-JSON response (status {resp.status_code})", "_mcp_http_status": 502}

    body["_mcp_http_status"] = resp.status_code
    return body
