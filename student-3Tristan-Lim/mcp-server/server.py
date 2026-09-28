from mcp.server.fastmcp import FastMCP

from tools import (
    get_staff_by_status,
    get_staff_count,
    list_project_files,
    read_ci_report,
)

mcp = FastMCP("Workload and Availability MCP")

AVAILABLE_TOOLS = [
    "staff_count",
    "staff_by_status",
    "project_files",
    "ci_report",
]


@mcp.tool()
def staff_count():
    return get_staff_count()


@mcp.tool()
def staff_by_status(status: str):
    return get_staff_by_status(status)


@mcp.tool()
def project_files(directory_path: str = ".."):
    return list_project_files(directory_path)


@mcp.tool()
def ci_report(report_path: str = "../reports/report.json"):
    return read_ci_report(report_path)


if __name__ == "__main__":
    print("Starting Workload and Availability MCP Server...")
    print("Server status: RUNNING")
    print("Interact with MCP tools from a second terminal.")
    print("Available tools:")
    for tool in AVAILABLE_TOOLS:
        print(f"- {tool}")
    mcp.run()
