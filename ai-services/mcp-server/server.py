from mcp.server.fastmcp import FastMCP

import tools


# ============================================================
# Common MCP Server
# ============================================================

mcp = FastMCP(
    "Faculty Management System MCP"
)

AVAILABLE_TOOLS = []


# ============================================================
# Student 1 - Staff Management
# ============================================================
#
# OWNER: Student 1
#
# Register Student 1 tools here.
#
# Pattern:
#
# @mcp.tool()
# def student1_<tool_name>(...):
#     return tools.student1_<tool_name>(...)
#
# AVAILABLE_TOOLS.append(
#     "student1_<tool_name>"
# )
#


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================
#
# OWNER: Student 2 - Hein
#
# Register Student 2 tools here.
#
# Planned initial tools:
#
# student2_validate_teaching_allocation
# student2_check_classroom_availability
#
# Pattern:
#
# @mcp.tool()
# def student2_<tool_name>(...):
#     return tools.student2_<tool_name>(...)
#
# AVAILABLE_TOOLS.append(
#     "student2_<tool_name>"
# )
#


# ============================================================
# Student 3 - Workload & Availability Management
# ============================================================
#
# OWNER: Student 3
#
# Register Student 3 shared-MCP tools here.
# Adapt existing feature-specific MCP registrations as required.
#


# ============================================================
# Student 4 - Research & Grant Management
# ============================================================
#
# OWNER: Student 4
#

@mcp.tool()
def student4_project_count(department: str = None, status: str = None):
    return tools.student4_project_count(department, status)

AVAILABLE_TOOLS.append("student4_project_count")


@mcp.tool()
def student4_projects_by_department(department: str):
    return tools.student4_projects_by_department(department)

AVAILABLE_TOOLS.append("student4_projects_by_department")


@mcp.tool()
def student4_project_grants_summary(project_id: int):
    return tools.student4_project_grants_summary(project_id)

AVAILABLE_TOOLS.append("student4_project_grants_summary")


@mcp.tool()
def student4_research_history(department: str):
    return tools.student4_research_history(department)

AVAILABLE_TOOLS.append("student4_research_history")


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================
#
# OWNER: Student 5
#
# Register Student 5 shared-MCP tools here.
#


# ============================================================
# Common Server Entry Point
# ============================================================

if __name__ == "__main__":
    print(
        "Starting Faculty Management System MCP Server..."
    )
    print(
        "Server status: RUNNING"
    )

    print(
        "Available tools:"
    )

    if AVAILABLE_TOOLS:
        for tool_name in AVAILABLE_TOOLS:
            print(
                f"- {tool_name}"
            )
    else:
        print(
            "- No feature tools registered yet."
        )

    # Lab 07 uses the MCP SDK's default local transport.
    # Transport may be updated later when final group backend
    # integration is implemented and validated.
    mcp.run()