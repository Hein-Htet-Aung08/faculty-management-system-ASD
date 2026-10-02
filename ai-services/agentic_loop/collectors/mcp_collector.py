import asyncio
import os
import re
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

REQUIRED_TRANSPORT = "streamable-http"

UNKNOWN_TOOL_PROBE = "zzzz_agentic_validation_unknown_tool_987654321"


def _describe(exc: BaseException) -> str:
    # asyncio TaskGroups wrap connection failures in an ExceptionGroup;
    # unwrap to the underlying cause for a readable message.
    causes = getattr(exc, "exceptions", None)
    if causes:
        return _describe(causes[0])
    return f"{type(exc).__name__}: {exc}"


def _is_downstream_error(result_text: str) -> bool:
    # Tools report their own feature-service failures as a structured
    # {"status": "error", ...} dict rather than raising - that is a
    # downstream risk to note, not an MCP transport failure.
    return '"status": "error"' in result_text or '"status":"error"' in result_text


def _student_of(tool_name: str):
    match = re.match(r"student(\d+)_", tool_name)
    return match.group(1) if match else None


async def _live_validate(mcp_url):
    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools = tools_result.tools

            if not tools:
                return False, "Live MCP server reported zero registered tools."

            callable_tools = []
            skipped_tools = []
            for tool in tools:
                if (tool.inputSchema or {}).get("required"):
                    skipped_tools.append(tool)
                else:
                    callable_tools.append(tool)

            if not callable_tools:
                return False, (
                    "No zero-argument tool is registered, so live validation "
                    "cannot safely invoke any tool without guessing arguments."
                )

            lines = []
            ok_count = 0
            downstream_error_count = 0
            tested_students = set()

            for tool in callable_tools:
                call_result = await session.call_tool(tool.name, {})

                if call_result.isError:
                    detail = call_result.content[0].text if call_result.content else ""
                    return False, (
                        f"Live call to {tool.name!r} reported an MCP-transport-level "
                        f"error (isError=True): {detail}"
                    )

                text = call_result.content[0].text if call_result.content else ""
                student = _student_of(tool.name)
                if student:
                    tested_students.add(student)

                if _is_downstream_error(text):
                    downstream_error_count += 1
                    lines.append(f"  - {tool.name} -> DOWNSTREAM ERROR: {text}")
                else:
                    ok_count += 1
                    lines.append(f"  - {tool.name} -> OK: {text}")

            for tool in skipped_tools:
                required = ", ".join((tool.inputSchema or {}).get("required", []))
                lines.append(f"  - {tool.name} -> SKIPPED (requires arguments: {required})")

            unknown_result = await session.call_tool(UNKNOWN_TOOL_PROBE, {})

            if not unknown_result.isError:
                return False, "Calling an unregistered tool name did not report isError=True."

            tested_count = len(callable_tools)
            invocation_report = (
                f"Live tool invocation ({tested_count} of {len(tools)} tools "
                f"safely callable with no arguments; {len(skipped_tools)} require "
                "arguments and were not blindly invoked):\n"
                + "\n".join(lines)
                + f"\nSummary: {ok_count}/{tested_count} invoked with a clean result, "
                f"{downstream_error_count} downstream feature-service failure(s), "
                f"0 MCP-transport failures"
            )

            return True, {
                "tool_count": len(tools),
                "tool_names": [tool.name for tool in tools],
                "tested_count": tested_count,
                "ok_count": ok_count,
                "downstream_error_count": downstream_error_count,
                "tested_students": sorted(tested_students),
                "invocation_report": invocation_report,
            }


def collect(app_dir, repo_root):
    app_dir = Path(app_dir)

    mcp_dir = app_dir.parent / "mcp-server"

    required_paths = [
        mcp_dir / "server.py",
        mcp_dir / "tools.py",
        mcp_dir / "requirements.txt",
    ]

    missing = [str(path) for path in required_paths if not path.is_file()]

    if missing:
        return False, "MCP evidence incomplete. Missing: " + ", ".join(missing)

    server_text = mcp_dir.joinpath("server.py").read_text(encoding="utf-8")

    transport_present = (
        f'transport="{REQUIRED_TRANSPORT}"' in server_text
        or f"transport='{REQUIRED_TRANSPORT}'" in server_text
    )

    if not transport_present:
        return False, (
            "MCP server does not run real MCP protocol over HTTP "
            f'(expected mcp.run(transport="{REQUIRED_TRANSPORT}") in server.py, '
            "so containerised backends on their own Docker networks could not reach it)."
        )

    registered_tools = re.findall(
        r'AVAILABLE_TOOLS\.append\(\s*"([a-zA-Z0-9_]+)"\s*\)',
        server_text,
    )

    if not registered_tools:
        return False, "No tools are registered in AVAILABLE_TOOLS in server.py."

    contributing_students = sorted(
        {
            match.group(1)
            for name in registered_tools
            if (match := re.match(r"student(\d+)_", name))
        }
    )

    requirements_text = mcp_dir.joinpath("requirements.txt").read_text(encoding="utf-8").lower()

    if "mcp" not in requirements_text:
        return False, "mcp-server/requirements.txt does not declare the mcp package."

    mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:5201/mcp")

    try:
        ok, detail = asyncio.run(_live_validate(mcp_url))
    except Exception as exc:
        return False, f"Live MCP protocol validation failed: {_describe(exc)}"

    if not ok:
        return False, detail

    evidence = (
        "MCP VALIDATION EVIDENCE\n"
        "- Structural files: PASS\n"
        f"- Transport: PASS (mcp.run(transport=\"{REQUIRED_TRANSPORT}\"))\n"
        f"- Statically registered tools: PASS ({len(registered_tools)} in server.py, "
        f"contributing students: {', '.join(contributing_students) or 'none'})\n"
        f"- requirements.txt declares mcp package: PASS\n"
        f"- Live tool listing: PASS ({detail['tool_count']} tool(s) reachable over "
        f"real MCP protocol at {mcp_url})\n"
        f"- {detail['invocation_report']}\n"
        f"- Live-tested students: {', '.join(detail['tested_students']) or 'none'} "
        f"(tools requiring arguments cannot be safely invoked blind, so their "
        "student may only be covered by static registration + live listing above)\n"
        "- Unknown-tool error handling: PASS (isError=True, no crash)\n"
    )

    return True, evidence
