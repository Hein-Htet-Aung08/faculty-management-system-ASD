
"""Read-only collection of Release 2 testing evidence."""

import re
from pathlib import Path


STUDENTS = range(1, 6)

SECURITY_CHECKS = {
    "ruff": ("ruff",),
    "detect-secrets": ("secret detection", "detect-secrets"),
    "pip-audit": ("dependency audit", "pip-audit"),
}


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def current_release2_test_count(student_dir):
    suite = student_dir / "tests" / "test_release2_endpoints.py"

    if not suite.is_file():
        return None

    return len(
        re.findall(
            r"(?m)^\s*def test_\w+\s*\(",
            read_text(suite),
        )
    )


def inspect_test_report(path, current_count):
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
        return (
            "FAILED",
            f"{fail_count} failures, {error_count} errors",
        )

    if pass_count is None:
        return "UNVERIFIED", "No pytest pass summary found"

    if current_count is not None and pass_count != current_count:
        return (
            "STALE_OR_INCOMPLETE",
            f"Saved: {pass_count} passed; "
            f"current Release 2 test definitions: {current_count}",
        )

    return "PASS_RECORDED", f"{pass_count} tests passed in snapshot"


def inspect_security_report(path):
    if not path.is_file():
        return "MISSING", "No saved security scan results"

    lines = read_text(path).splitlines()
    outcomes = {}

    for check_name, aliases in SECURITY_CHECKS.items():
        matching = [
            line
            for line in lines
            if any(alias in line.lower() for alias in aliases)
        ]

        if not matching:
            outcomes[check_name] = "MISSING"
            continue

        statuses = [
            match.group(1).lower()
            for line in matching
            if (match := re.search(
                r"\b(Passed|Failed)\s*$",
                line,
                re.IGNORECASE,
            ))
        ]

        if "failed" in statuses:
            outcomes[check_name] = "FAILED"
        elif statuses and all(s == "passed" for s in statuses):
            outcomes[check_name] = "PASS_RECORDED"
        else:
            outcomes[check_name] = "UNVERIFIED"

    if all(value == "PASS_RECORDED" for value in outcomes.values()):
        return "PASS_RECORDED", str(outcomes)

    if "FAILED" in outcomes.values():
        return "FAILED", str(outcomes)

    return "INCOMPLETE", str(outcomes)


def collect(app_dir, repo_root):
    root = Path(repo_root)
    workflows_dir = root / ".github" / "workflows"

    results = []
    saved_report_count = 0

    for number in STUDENTS:
        directories = sorted(
            path for path in root.glob(f"student-{number}*")
            if path.is_dir()
        )

        if not directories:
            results.append({
                "student": number,
                "status": "NOT_READY",
                "reason": "Student directory missing",
            })
            continue

        student_dir = directories[0]
        reports_dir = student_dir / "reports" / "release2"

        workflows = (
            list(workflows_dir.glob(f"student-{number}-*.yml"))
            + list(workflows_dir.glob(f"student-{number}-*.yaml"))
        )

        endpoint_path = reports_dir / "endpoint-tests.txt"
        security_path = reports_dir / "precommit-results.txt"

        saved_report_count += int(endpoint_path.is_file())
        saved_report_count += int(security_path.is_file())

        current_count = current_release2_test_count(student_dir)

        test_status, test_detail = inspect_test_report(
            endpoint_path, current_count
        )

        security_status, security_detail = inspect_security_report(
            security_path
        )

        # A CI YAML file proves configuration exists,
        # not that GitHub Actions executed successfully.
        ci_configuration = (
            "PRESENT" if workflows else "MISSING"
        )

        status = "EVIDENCE_PRESENT"

        if (
            ci_configuration != "PRESENT"
            or test_status != "PASS_RECORDED"
            or security_status != "PASS_RECORDED"
        ):
            status = "REVIEW_REQUIRED"

        results.append({
            "student": number,
            "directory": student_dir.name,
            "status": status,
            "ci_configuration": ci_configuration,
            "ci_execution": "NOT_VERIFIED_FROM_LOCAL_FILES",
            "test_status": test_status,
            "test_detail": test_detail,
            "security_status": security_status,
            "security_detail": security_detail,
        })

    if saved_report_count == 0:
        return (
            False,
            "OBSERVE FAILED: No saved Release 2 testing "
            "or security results were found.",
        )

    incomplete = [
        item["student"]
        for item in results
        if item["status"] != "EVIDENCE_PRESENT"
    ]

    verdict = (
        "NOT_READY"
        if incomplete
        else "HUMAN_VALIDATION_REQUIRED"
    )

    lines = [
        "TESTING REPORT REVIEW EVIDENCE",
        "Collection method: read-only local report inspection",
        f"Students inspected: {len(results)}",
        f"Saved evidence files: {saved_report_count}",
        f"Students with incomplete evidence: {incomplete}",
        f"DETERMINISTIC VERDICT: {verdict}",
        "CI workflow files are configuration, not execution proof.",
        "Recorded PASS results may be stale or from an older commit.",
        "No live GitHub Actions results were fetched.",
        "",
    ]

    for result in results:
        lines.append(
            f"Student {result['student']}: {result['status']}"
        )

        for field, value in result.items():
            if field not in {"student", "status"}:
                lines.append(f"  {field}: {value}")

        lines.append("")

    return True, "\n".join(lines)
