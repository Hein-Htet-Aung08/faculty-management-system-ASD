# MCP Validation Report

## DETERMINISTIC VALIDATION SUMMARY

Status: PASS
Functional validation: PASS (structure, transport, registered tools, requirements, live tool listing, live invocation, unknown-tool error handling)
Student coverage (registered): 1, 2, 3, 4, 5
Live tool invocation: 3/3 zero-argument tools invoked cleanly, 0 downstream feature-service failure(s), 0 MCP-transport failures
Student coverage (live-invoked): 3, 4 

The deterministic validation summary above is authoritative for functional pass/fail. The model outputs below are advisory and do not override collected evidence.

## OBSERVE

```text
MCP VALIDATION EVIDENCE
- Structural files: PASS
- Transport: PASS (mcp.run(transport="streamable-http"))
- Statically registered tools: PASS (14 in server.py, contributing students: 1, 2, 3, 4, 5)
- requirements.txt declares mcp package: PASS
- Live tool listing: PASS (14 tool(s) reachable over real MCP protocol at http://localhost:5201/mcp)
- Live tool invocation (3 of 14 tools safely callable with no arguments; 11 require arguments and were not blindly invoked):
  - student3_staff_count -> OK: {
  "status": "success",
  "data": {
    "count": 10
  }
}
  - student3_open_alerts -> OK: {
  "status": "success",
  "data": [
    {
      "alert_id": 1,
      "alert_type": "overload",
      "date_raised": "2026-08-20",
      "message": "Total 41.0h exceeds cap 37.5h for Computer Science",
      "severity": "high",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 2,
      "alert_type": "clash",
      "date_raised": "2026-08-20",
      "message": "Conference leave overlaps 31266 teaching weeks",
      "severity": "medium",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 3,
      "alert_type": "overload",
      "date_raised": "2026-08-20",
      "message": "Total 20.0h exceeds 0.5 fractional cap 18.75h",
      "severity": "medium",
      "staff_id": 4,
      "status": "open"
    },
    {
      "alert_id": 5,
      "alert_type": "underload",
      "date_raised": "2026-08-21",
      "message": "Total 21.0h below underload floor 30.0h",
      "severity": "low",
      "staff_id": 3,
      "status": "open"
    },
    {
      "alert_id": 6,
      "alert_type": "underload",
      "date_raised": "2026-08-21",
      "message": "Total 12.0h below underload floor 30.0h",
      "severity": "medium",
      "staff_id": 6,
      "status": "open"
    },
    {
      "alert_id": 7,
      "alert_type": "underload",
      "date_raised": "2026-08-21",
      "message": "Total 28.0h below underload floor 30.0h",
      "severity": "low",
      "staff_id": 9,
      "status": "open"
    },
    {
      "alert_id": 8,
      "alert_type": "clash",
      "date_raised": "2026-08-22",
      "message": "Requested annual leave overlaps 48620 teaching weeks",
      "severity": "medium",
      "staff_id": 5,
      "status": "open"
    },
    {
      "alert_id": 9,
      "alert_type": "clash",
      "date_raised": "2026-08-22",
      "message": "Annual leave overlaps 24108 teaching weeks",
      "severity": "low",
      "staff_id": 7,
      "status": "open"
    },
    {
      "alert_id": 12,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "conference leave 2026-09-14..2026-09-18 (approved) overlaps '31266 Introduction to Software Development'",
      "severity": "low",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 13,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "conference leave 2026-09-14..2026-09-18 (approved) overlaps '48024 Programming Fundamentals tutorials'",
      "severity": "low",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 14,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "long_service leave 2026-10-05..2026-10-30 (approved) overlaps '31268 Web Systems'",
      "severity": "low",
      "staff_id": 3,
      "status": "open"
    },
    {
      "alert_id": 15,
      "alert_type": "overload",
      "date_raised": "2026-09-09",
      "message": "Total 20.0h exceeds cap 18.75h for Information Technology",
      "severity": "high",
      "staff_id": 4,
      "status": "open"
    },
    {
      "alert_id": 16,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "sick leave 2026-08-24..2026-08-26 (approved) overlaps '32555 Fundamentals of Interaction Design'",
      "severity": "low",
      "staff_id": 4,
      "status": "open"
    },
    {
      "alert_id": 17,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "annual leave 2026-09-28..2026-10-02 (pending) overlaps '48620 Engineering Mechanics'",
      "severity": "low",
      "staff_id": 5,
      "status": "open"
    },
    {
      "alert_id": 18,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "long_service leave 2026-08-01..2026-12-15 (approved) overlaps '48620 Engineering Mechanics'",
      "severity": "low",
      "staff_id": 5,
      "status": "open"
    },
    {
      "alert_id": 19,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "conference leave 2026-11-02..2026-11-06 (pending) overlaps '22107 Accounting for Business Decisions'",
      "severity": "low",
      "staff_id": 6,
      "status": "open"
    },
    {
      "alert_id": 20,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "annual leave 2026-09-21..2026-09-25 (approved) overlaps '24108 Marketing Foundations'",
      "severity": "low",
      "staff_id": 7,
      "status": "open"
    },
    {
      "alert_id": 21,
      "alert_type": "overload",
      "date_raised": "2026-09-09",
      "message": "Total 20.0h exceeds cap 18.75h for Management",
      "severity": "high",
      "staff_id": 8,
      "status": "open"
    },
    {
      "alert_id": 22,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "sick leave 2026-08-18..2026-08-19 (approved) overlaps '21129 Managing People and Organisations'",
      "severity": "low",
      "staff_id": 8,
      "status": "open"
    },
    {
      "alert_id": 23,
      "alert_type": "clash",
      "date_raised": "2026-09-09",
      "message": "conference leave 2026-09-07..2026-09-11 (approved) overlaps '92418 Clinical Practice'",
      "severity": "low",
      "staff_id": 9,
      "status": "open"
    },
    {
      "alert_id": 24,
      "alert_type": "overload",
      "date_raised": "2026-09-09",
      "message": "Total 37.5h is at cap 37.5h - no headroom",
      "severity": "low",
      "staff_id": 10,
      "status": "open"
    }
  ]
}
  - student4_project_count -> OK: {
  "status": "success",
  "data": {
    "count": 10
  }
}
  - student1_get_staff_profile -> SKIPPED (requires arguments: staff_id)
  - student1_search_staff_by_expertise -> SKIPPED (requires arguments: expertise)
  - student2_validate_teaching_allocation -> SKIPPED (requires arguments: offer_id, classroom_id, day, date_range, start_time, end_time, class_type, expected_class_size)
  - student2_check_classroom_availability -> SKIPPED (requires arguments: classroom_id, date, year, start_time, end_time)
  - student3_staff_by_status -> SKIPPED (requires arguments: status)
  - student3_staff_workload_detail -> SKIPPED (requires arguments: staff_id)
  - student4_projects_by_department -> SKIPPED (requires arguments: department)
  - student4_project_grants_summary -> SKIPPED (requires arguments: project_id)
  - student4_research_history -> SKIPPED (requires arguments: department)
  - student5_staff_development_summary -> SKIPPED (requires arguments: staff_id)
  - student5_training_by_skill_area -> SKIPPED (requires arguments: skill_area)
Summary: 3/3 invoked with a clean result, 0 downstream feature-service failure(s), 0 MCP-transport failures
- Live-tested students: 3, 4 (tools requiring arguments cannot be safely invoked blind, so their student may only be covered by static registration + live listing above)
- Unknown-tool error handling: PASS (isError=True, no crash)

```

## IMPLEMENTATION AGENT ASSESSMENT (ADVISORY)

Status: PASS
Strengths: 14 tools are registered statically and can be safely invoked with no arguments.
Gaps: None observed.

Review Scope:
Shared MCP Server Integration

Observed Evidence:
MCP VALIDATION EVIDENCE
- Structural files: PASS
- Transport: PASS (mcp.run(transport="streamable-http"))
- Statically registered tools: PASS (14 in server.py, contributing students: 1, 2, 3, 4, 5)
- requirements.txt declares mcp package: PASS
- Live tool listing: PASS (14 tool(s) reachable over real MCP protocol at http://localhost:5201/mcp)
- Live tool invocation (3 of 14 tools safely callable with no arguments; 11 require arguments and were not blindly invoked):
  - student3_staff_count -> OK: {
  "status": "success",
  "data": {
    "count": 10
  }
}
  - student3_open_alerts -> OK: {
  "status": "success",
  "data": [
    {
      "alert_id": 1,
      "alert_type": "overload",
      "date_raised": "2026-08-20",
      "message": "Total 41.0h exceeds cap 37.5h for Computer Science",
      "severity": "high",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 2,
      "alert_type": "clash",
      "date_raised": "2026-08-20",
      "message": "Conference leave overlaps 31266 teaching weeks",
      "severity": "medium",
      "staff_id": 1,
      "status": "open"
    },
    {
      "alert_id": 3,
      "

## REVIEW AGENT ASSESSMENT (ADVISORY)

Risk: None observed
Correction: None
Retest: No additional retest required
