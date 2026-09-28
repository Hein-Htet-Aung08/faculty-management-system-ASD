from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Faculty Management MCP")

# ============================================================
# Each student registers their own tools below, in their own
# block, using @mcp.tool() the same way Student 4's block does.
# Do not edit anyone else's block.
# ============================================================

# --- Student 1: Andy Lam (Staff Management) ---
# from student_1_andy.tools import (
#     your_function_one,
#     your_function_two,
# )
#
# @mcp.tool()
# def your_tool_name(...):
#     return your_function_one(...)

# --- Student 2: Hein Htet Aung (Teaching, Subject & Classroom Allocation) ---
# from student_2_hein.tools import ...
#
# @mcp.tool()
# def your_tool_name(...):
#     ...

# --- Student 3: Tristan Lim (Workload & Availability Management) ---
# from student_3_tristan.tools import ...
#
# @mcp.tool()
# def your_tool_name(...):
#     ...

# --- Student 4: Nicholas Hatzidimitriou (Research & Grant Management) ---
from student_4_nicholas.tools import (
    get_project_count,
    search_projects_by_department,
    get_project_grants_summary,
    get_research_history_for_department,
)

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

# --- Student 5: Matthew Barnard (Performance & Professional Development) ---
# from student_5_matthew.tools import ...
#
# @mcp.tool()
# def your_tool_name(...):
#     ...

if __name__ == "__main__":
    print("Starting Research and Grant Management MCP Server...")
    print("Available tools:")
    for tool in AVAILABLE_TOOLS:
        print(f"- {tool}")
    mcp.run()
