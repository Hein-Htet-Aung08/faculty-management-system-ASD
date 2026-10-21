
"""Read-only evidence collection for Release 2 Multi-Agent review."""

import json
from collections import defaultdict
from pathlib import Path


REQUIRED_EVENTS = {
    "workflow_started",
    "planner_completed",
    "evidence_collected",
    "worker_completed",
    "automated_checks_completed",
    "reviewer_completed",
    "awaiting_human_review",
}

AGENTS = (
    "planner_agent",
    "worker_agent",
    "reviewer_agent",
)

EXPECTED_FEATURES = {
    "student1",
    "student2",
    "student3",
    "student4",
    "student5",
}

def read_jsonl(path):
    records = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{path}:{line_number}: invalid JSON"
            ) from exc

        if not isinstance(record, dict):
            raise ValueError(
                f"{path}:{line_number}: expected JSON object"
            )

        records.append(record)

    return records


def collect(app_dir, repo_root):
    root = Path(repo_root)

    # Prefer committed, reproducible snapshots over runtime logs.
    snapshots = sorted(
        root.glob("student-*/reports/release2/multi-agent")
    )

    runtime = (
        Path(app_dir).parent
        / "multi-agent-server"
    )

    sources = snapshots + [runtime]

    seen_workflows = set()
    results = []
    warnings = []

    for source in sources:
        history_path = source / "workflow_history.jsonl"
        audit_path = source / "coordination_audit.jsonl"

        if not history_path.exists() and not audit_path.exists():
            continue

        if not history_path.is_file() or not audit_path.is_file():
            warnings.append(
                f"{source}: missing workflow history or audit log"
            )
            continue

        try:
            history = read_jsonl(history_path)
            audit = read_jsonl(audit_path)
        except (OSError, ValueError) as exc:
            warnings.append(str(exc))
            continue

        decisions = {}
        audit_events = defaultdict(set)

        for record in history:
            if record.get("event") == "human_decision":
                decisions[record.get("workflow_id")] = record

        for record in audit:
            workflow_id = record.get("workflow_id")
            event = record.get("event")

            if workflow_id and event:
                audit_events[workflow_id].add(event)

        for workflow in history:
            if workflow.get("event") != "workflow":
                continue

            workflow_id = workflow.get("workflow_id")

            if not workflow_id:
                warnings.append(
                    f"{history_path}: workflow without ID"
                )
                continue

            if workflow_id in seen_workflows:
                continue

            seen_workflows.add(workflow_id)

            decision = decisions.get(workflow_id)
            checks = workflow.get("automated_checks", [])

            if not isinstance(checks, list):
                checks = []

            failed_checks = [
                check.get("check", "unknown")
                for check in checks
                if isinstance(check, dict)
                and check.get("passed") is not True
            ]

            missing_events = REQUIRED_EVENTS - audit_events[workflow_id]

            if decision is not None:
                if "human_decision_recorded" not in audit_events[workflow_id]:
                    missing_events.add("human_decision_recorded")

            agent_statuses = {
                "planner_agent": workflow.get(
                    "planner_result", {}
                ).get("status"),
                "worker_agent": workflow.get(
                    "worker_result", {}
                ).get("status"),
                "reviewer_agent": workflow.get(
                    "reviewer_result", {}
                ).get("status"),
            }

            problems = []

            for agent, status in agent_statuses.items():
                if status != "success":
                    problems.append(
                        f"{agent} status={status}"
                    )

            evidence_count = workflow.get(
                "worker_result", {}
            ).get("evidence_count", 0)

            if not isinstance(evidence_count, int) or evidence_count <= 0:
                problems.append("worker has no recorded evidence")

            if not checks:
                problems.append("automated checks are missing")

            if failed_checks:
                problems.append(
                    "failed checks: " + ", ".join(failed_checks)
                )

            if missing_events:
                problems.append(
                    "missing audit events: "
                    + ", ".join(sorted(missing_events))
                )

            if decision is None:
                problems.append("human decision pending")
                decision_label = "PENDING"
            else:
                decision_label = decision.get(
                    "decision", "UNKNOWN"
                )

                if decision_label != "Accept":
                    problems.append(
                        f"human decision: {decision_label}"
                    )

            quality = (
                "NO_IDENTIFIED_ISSUES"
                if not problems
                else "REVIEW_REQUIRED"
            )

            source_name = str(
                source.relative_to(root)
            )

            results.append(
                {
                    "workflow_id": workflow_id,
                    "feature": workflow.get(
                        "feature", "unknown"
                    ),
                    "source": source_name,
                    "agent_statuses": agent_statuses,
                    "evidence_count": evidence_count,
                    "checks_total": len(checks),
                    "failed_checks": failed_checks,
                    "human_decision": decision_label,
                    "missing_audit_events": sorted(missing_events),
                    "quality": quality,
                    "problems": problems,
                }
            )

    if not results:
        detail = "\n".join(warnings) or (
            "No workflow evidence found. "
            "Run a workflow and save its JSONL audit files."
        )

        return False, f"OBSERVE FAILED:\n{detail}"

    observed_features = {
        item["feature"]
        for item in results
    }

    missing_features = sorted(
        EXPECTED_FEATURES - observed_features
    )

    group_coverage = (
        "COMPLETE"
        if not missing_features
        else "INCOMPLETE"
    )

    lines = [
        "MULTI-AGENT WORKFLOW REVIEW EVIDENCE",
        "Collection method: read-only JSONL inspection",
        f"Workflows inspected: {len(results)}",
        f"Group coverage: {group_coverage}",
        f"Features with evidence: {sorted(observed_features)}",
        f"Features without evidence: {missing_features}",
        "Note: evidence validation does not equal release approval.",
        "",
    ]

    for item in results:
        lines.extend(
            [
                f"Workflow: {item['workflow_id']}",
                f"Feature: {item['feature']}",
                f"Source: {item['source']}",
                f"Agent statuses: {item['agent_statuses']}",
                f"Worker evidence count: {item['evidence_count']}",
                f"Automated checks: {item['checks_total']}",
                f"Failed checks: {item['failed_checks']}",
                f"Human decision: {item['human_decision']}",
                f"Missing audit events: {item['missing_audit_events']}",
                f"Assessment: {item['quality']}",
                f"Findings: {item['problems'] or ['None identified']}",
                "",
            ]
        )

    if warnings:
        lines.append("ADDITIONAL WARNINGS:")
        lines.extend(warnings)

    return True, "\n".join(lines)
