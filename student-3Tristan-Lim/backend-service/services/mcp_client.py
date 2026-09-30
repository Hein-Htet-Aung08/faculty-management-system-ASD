import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://host.docker.internal:5201/mcp")


async def _call_tool(tool_name: str, args: dict):
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, args)


def _describe(exc: BaseException) -> str:
    # asyncio TaskGroups wrap connection failures in an ExceptionGroup;
    # unwrap to the underlying cause for a readable message.
    causes = getattr(exc, "exceptions", None)
    if causes:
        return _describe(causes[0])
    return str(exc)


def mcp_invoke(tool_name: str, args: dict) -> dict:
    try:
        result = asyncio.run(_call_tool(tool_name, args))
    except Exception as e:
        return {"status": "error", "error": f"MCP server unavailable: {_describe(e)}", "_mcp_http_status": 503}

    text = result.content[0].text if result.content else ""

    if result.isError:
        status = 404 if text.startswith("Unknown tool") else 400
        return {"status": "error", "error": text, "_mcp_http_status": status}

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {"status": "error", "error": f"Unexpected MCP response: {text}", "_mcp_http_status": 502}
