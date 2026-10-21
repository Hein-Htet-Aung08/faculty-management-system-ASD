"""Release 2 testing review: saved evidence or opt-in fresh local testing.

The collector never changes student feature code or databases. Live tests
execute only explicitly allowlisted test suites in separate processes.
"""

import os
import re
from pathlib import Path

from collectors import fresh_test_runner


STUDENTS = range(1, 6)
SECURITY_CHECKS = {
    "ruff": ("ruff",),
    "detect-secrets": ("secret detection", "detect-secrets"),
    "pip-audit": ("dependency audit", "pip-audit"),
}


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def current_release2_test_count(student_dir):
    suite = Path(student_dir) / "tests" / "test_release2_endpoints.py"
    if not suite.is_file():
        return None
    return len(re.findall(r"(?m)^\s*def test_\w+\s*\(", read_text(suite)))


def inspect_test_report(path, current_count):
    path = Path(path)
    if not path.is_file():
        return "MISSING", "No saved endpoint test report"
    content = read_text(path)
    passed = re.search(r"\b(\d+)\s+passed\b", content)
    failed = re.search(r"\b(\d+)\s+failed\b", content)
    errors = re.search(r"\b(\d+)\s+errors?\b", content)
    pass_count = int(passed.group(1)) if passed else None
    fail_count = int(failed.group(1)) if failed else 0
    error_count = int(errors.group(1)) if errors else 0
    if fail_count or error_count:
        return "FAILED", f"{fail_count} failures, {error_count} errors"
    if pass_count is None:
        return "UNVERIFIED", "No pytest pass summary found"
    if current_count is not None and pass_count != current_count:
        return (
            "STALE_OR_INCOMPLETE",
            f"Saved: {pass_count} passed; current Release 2 test definitions: {current_count}",
        )
    return "PASS_RECORDED", f"{pass_count} tests passed in saved snapshot; commit unverified"


def inspect_security_report(path):
    path = Path(path)
    if not path.is_file():
        return "MISSING", "No saved security scan results"
    lines = read_text(path).splitlines()
    outcomes = {}
    for check_name, aliases in SECURITY_CHECKS.items():
        matching = [
            line for line in lines
            if any(alias in line.lower() for alias in aliases)
        ]
        if not matching:
            outcomes[check_name] = "MISSING"
            continue
        statuses = [
            match.group(1).lower()
            for line in matching
            if (match := re.search(r"\b(Passed|Failed)\s*$", line, re.IGNORECASE))
        ]
        if "failed" in statuses:
            outcomes[check_name] = "FAILED"
        elif statuses and all(status == "passed" for status in statuses):
            outcomes[check_name] = "PASS_RECORDED"
        else:
            outcomes[check_name] = "UNVERIFIED"
    if all(status == "PASS_RECORDED" for status in outcomes.values()):
        return "PASS_RECORDED", str(outcomes)
    if "FAILED" in outcomes.values():
        return "FAILED", str(outcomes)
    return "INCOMPLETE", str(outcomes)


def _student_dir(root, number):
    matching = sorted(
        directory for directory in root.glob(f"student-{number}*")
        if directory.is_dir()
    )
    return matching[0] if matching else None


def collect(app_dir, repo_root):
    """Return (collected, evidence_text); a successful collection is not approval."""
    root = Path(repo_root).resolve()
    mode = os.getenv("AGENTIC_TEST_RUN_MODE", "saved").strip().lower()
    if mode not in {"saved", "fresh"}:
        return False, "OBSERVE FAILED: unknown test collection mode"

    fresh = None
    ci_statuses = {n: "NOT_CHECKED_IN_SAVED_MODE" for n in STUDENTS}
    ci_detail = "GitHub Actions was not queried in saved-report mode."

    if mode == "fresh":
        try:
            fresh = fresh_test_runner.run_local_suites(root)
        except (OSError, ValueError) as exc:
            return False, f"OBSERVE FAILED: fresh execution failed: {type(exc).__name__}: {exc}"
        if fresh["local_tracked_changes"]:
            # CI is at a committed SHA, not the currently modified working tree.
            ci_statuses = {n: "NOT_COMPARABLE_TO_LOCAL_CHANGES" for n in STUDENTS}
            ci_detail = "CI not queried: local tracked files have uncommitted modifications"
        else:
            ci_statuses, ci_detail = fresh_test_runner.check_current_commit_ci(fresh["commit"])

    rows = []
    saved_reports = 0

    for number in STUDENTS:
        directory = _student_dir(root, number)
        if directory is None:
            rows.append({"number": number, "status": "NOT_READY", "reason": "Student folder missing"})
            continue

        report_dir = directory / "reports" / "release2"
        endpoint_path = report_dir / "endpoint-tests.txt"
        security_path = report_dir / "precommit-results.txt"
        saved_reports += int(endpoint_path.is_file()) + int(security_path.is_file())

        ci_file = root / ".github" / "workflows" / fresh_test_runner.WORKFLOWS[number]
        security_status, security_detail = inspect_security_report(security_path)

        row = {
            "number": number,
            "directory": directory.name,
            "ci_configuration": "PRESENT" if ci_file.is_file() else "MISSING",
            "ci_execution": ci_statuses[number],
            "security_status": security_status,
            "security_details": security_detail,
        }

        if mode == "fresh":
            suites = fresh["students"].get(number, [])
            if not suites:
                row["local_tests"] = "NOT_CONFIGURED_LOCAL_TESTS"
                row["suite_details"] = "Docker/service smoke tests require isolated CI"
            else:
                row["local_tests"] = (
                    "PASS" if all(s["status"] == "PASS" for s in suites)
                    else "FAILED_OR_INCOMPLETE"
                )
                row["suite_details"] = "; ".join(
                    f"{s['suite']}={s['status']} "
                    f"(tests={s.get('test_count')}, exit={s.get('exit_code')}, "
                    f"log={s.get('log', 'none')})"
                    for s in suites
                )
            row["saved_endpoint_report"] = "NOT_USED_FOR_FRESH_RESULT"
        else:
            current_count = current_release2_test_count(directory)
            test_status, test_details = inspect_test_report(endpoint_path, current_count)
            row["local_tests"] = test_status
            row["suite_details"] = test_details
            row["saved_endpoint_report"] = test_status

        verified = (
            row["local_tests"] == "PASS"
            and row["ci_execution"] == "SUCCESS_AT_COMMIT"
            and row["security_status"] == "PASS_RECORDED"
            and row["ci_configuration"] == "PRESENT"
        )
        # A saved security PASS is not commit-bound; still require human validation.
        row["status"] = "EVIDENCE_COLLECTED_HUMAN_REVIEW_REQUIRED" if verified else "REVIEW_REQUIRED"
        rows.append(row)

    if mode == "saved" and not saved_reports:
        return False, "OBSERVE FAILED: No saved Release 2 testing or security reports found"

    incomplete = [row["number"] for row in rows if row["status"] == "REVIEW_REQUIRED"]
    verdict = "NOT_READY" if incomplete else "HUMAN_VALIDATION_REQUIRED"

    lines = [
        "TESTING REPORT REVIEW EVIDENCE",
        f"Collection mode: {mode.upper()}",
        f"Students inspected: {len(rows)}",
        f"Students requiring more evidence: {incomplete}",
        f"DETERMINISTIC VERDICT: {verdict}",
        "This verdict uses test exit codes and available artifacts, not AI judgement.",
        "CI success requires a run at the EXACT current Git commit.",
        "Saved security scan results do not prove scans ran at the current commit.",
        f"CI verification: {ci_detail}",
    ]
    if mode == "fresh":
        lines.extend([
            f"Fresh local test execution: {fresh['timestamp']}",
            f"Local git HEAD: {fresh['commit']}",
            f"Local branch: {fresh['branch']}",
            f"Uncommitted tracked changes: {fresh['local_tracked_changes']}",
            f"Machine-readable run evidence: {fresh['summary_path']}",
            "Local test suites run in separate processes with temporary DB paths.",
            "Docker smoke tests are NOT executed locally by this mode.",
        ])
    else:
        lines.extend([
            f"Saved evidence files found: {saved_reports}",
            "Saved test results are NOT proven current merely by matching test counts.",
            "No fresh endpoint tests were executed.",
        ])

    lines.append("")
    for row in rows:
        lines.append(f"Student {row['number']}: {row['status']}")
        for key, value in row.items():
            if key not in {"number", "status"}:
                lines.append(f"  {key}: {value}")
        lines.append("")

    return True, "\n".join(lines)
