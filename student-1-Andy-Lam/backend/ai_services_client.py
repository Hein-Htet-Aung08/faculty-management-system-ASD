import asyncio
import json
import os

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Both integrations are OFF unless explicitly enabled, so CI and plain local
# runs work without the shared MCP/RAG servers. docker-compose turns them on.
MCP_ENABLED = os.getenv("MCP_ENABLED", "false").lower() == "true"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:5201/mcp")
MCP_TIMEOUT_SECONDS = float(os.getenv("MCP_TIMEOUT_SECONDS", "20"))

RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://localhost:5200")
# Grounded answers wait on the local LLM, so allow longer than a normal API call
RAG_TIMEOUT_SECONDS = float(os.getenv("RAG_TIMEOUT_SECONDS", "130"))

INSUFFICIENT_CONTEXT = "Insufficient context."


class AIServiceError(Exception):
    """Raised when a shared AI service cannot be reached or returns an unusable reply."""


def _root_cause(exc):
    # The MCP client runs inside anyio task groups, which wrap connection
    # failures in an ExceptionGroup -- unwrap to the readable underlying error
    while getattr(exc, "exceptions", None):
        exc = exc.exceptions[0]
    return exc


async def _call_tool_async(tool_name, arguments):
    async with streamablehttp_client(MCP_SERVER_URL, timeout=MCP_TIMEOUT_SECONDS) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments)


def call_mcp_tool(tool_name, arguments):
    """
    Calls a tool on the shared MCP server over streamable HTTP and returns the
    tool's structured (dict) result. Tool-level failures (e.g. staff not found)
    come back as a normal dict with status "error" -- only transport/protocol
    problems raise AIServiceError.
    """
    try:
        result = asyncio.run(
            asyncio.wait_for(_call_tool_async(tool_name, arguments), MCP_TIMEOUT_SECONDS)
        )
    except asyncio.TimeoutError as e:
        raise AIServiceError(
            f"MCP server did not respond within {MCP_TIMEOUT_SECONDS} seconds"
        ) from e
    except Exception as e:
        raise AIServiceError(
            f"Could not reach MCP server at {MCP_SERVER_URL}: {_root_cause(e)}"
        ) from e

    text = result.content[0].text if result.content else ""

    if result.isError:
        raise AIServiceError(f"MCP tool '{tool_name}' failed: {text}")

    try:
        return json.loads(text)
    except ValueError as e:
        raise AIServiceError(f"Unexpected MCP response: {text[:200]}") from e


def _post_rag(path, payload):
    url = f"{RAG_SERVER_URL.rstrip('/')}/{path}"
    try:
        response = requests.post(url, json=payload, timeout=RAG_TIMEOUT_SECONDS)
    except requests.Timeout as e:
        raise AIServiceError(
            f"RAG server did not respond within {RAG_TIMEOUT_SECONDS} seconds"
        ) from e
    except requests.RequestException as e:
        raise AIServiceError(f"Could not reach RAG server at {RAG_SERVER_URL}") from e

    try:
        return response.json()
    except ValueError as e:
        raise AIServiceError(f"Unexpected RAG response (HTTP {response.status_code})") from e


def ask_rag(question):
    """
    Asks the shared RAG server for a grounded answer and normalises the reply
    for the frontend. `insufficient_context` is True either when retrieval found
    nothing relevant, or when the model itself declined to answer from the
    retrieved context -- in both cases no citations are shown, since nothing
    was actually used to support an answer.
    """
    data = _post_rag("answer", {"query": question, "caller": "student1-staff-management"})

    if data.get("status") != "success":
        detail = data.get("details") or data.get("error") or "unknown error"
        raise AIServiceError(f"RAG server could not answer: {detail}")

    answer = (data.get("answer") or "").strip()
    insufficient = not answer or answer.lower().startswith(INSUFFICIENT_CONTEXT.lower().rstrip("."))

    return {
        "question": question,
        "answer": INSUFFICIENT_CONTEXT if insufficient else answer,
        "insufficient_context": insufficient,
        "confidence_category": "Insufficient" if insufficient else data.get("confidence_category"),
        "citations": [] if insufficient else data.get("citations", []),
    }


def refresh_rag_corpus():
    """Rebuilds the shared RAG index so it picks up the latest staff records."""
    data = _post_rag("refresh", {"caller": "student1-staff-management"})

    if data.get("status") != "success":
        raise AIServiceError(f"RAG refresh failed: {data.get('error', 'unknown error')}")

    return {"chunk_count": data.get("chunk_count")}
