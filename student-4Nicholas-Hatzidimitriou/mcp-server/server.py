from mcp.server.fastmcp import FastMCP
from tools import (
    get_project_count,
    search_projects_by_department,
    get_project_grants_summary,
    get_research_history_for_department,
)

mcp = FastMCP("Research and Grant Management MCP")

AVAILABLE_TOOLS = [
    "project_count",
    "projects_by_department",
    "project_grants_summary",
    "research_history",
]

@mcp.tool()
def project_count():
    return get_project_count()

@mcp.tool()
def projects_by_department(department: str):
    return search_projects_by_department(department)

@mcp.tool()
def project_grants_summary(project_id: int):
    return get_project_grants_summary(project_id)

@mcp.tool()
def research_history(department: str):
    return get_research_history_for_department(department)

if __name__ == "__main__":
    print("Starting Research and Grant Management MCP Server...")
    print("Available tools:")
    for tool in AVAILABLE_TOOLS:
        print(f"- {tool}")
    mcp.run()
