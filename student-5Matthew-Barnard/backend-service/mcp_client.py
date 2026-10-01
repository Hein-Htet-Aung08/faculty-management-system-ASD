import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPServiceError(Exception):
    pass


def enabled():
    return os.getenv("MCP_ENABLED", "false").lower() == "true"


async def _call_tool(tool_name, arguments):
    url = os.getenv("MCP_SERVER_URL", "http://localhost:5201/mcp")
    timeout = float(os.getenv("MCP_TIMEOUT", "20"))
    async with streamablehttp_client(url, timeout=timeout) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments)


def _error_message(error):
    causes = getattr(error, "exceptions", None)
    return _error_message(causes[0]) if causes else str(error)


def call_tool(tool_name, arguments):
    try:
        result = asyncio.run(_call_tool(tool_name, arguments))
    except Exception as exc:
        raise MCPServiceError(f"MCP server is unavailable: {_error_message(exc)}") from exc

    if result.isError or not result.content:
        detail = result.content[0].text if result.content else "empty tool response"
        raise MCPServiceError(f"MCP tool failed: {detail}")

    try:
        response = json.loads(result.content[0].text)
    except (ValueError, AttributeError) as exc:
        raise MCPServiceError("MCP server returned an invalid response") from exc
    if not isinstance(response, dict):
        raise MCPServiceError("MCP server returned an invalid response")
    return response
