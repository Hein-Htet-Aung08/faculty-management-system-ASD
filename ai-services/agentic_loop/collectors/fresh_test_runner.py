"""Explicitly authorised local test execution for Release 2 review.

Only fixed test commands listed in SAFE_SUITES can run. Never invoke the
team's Docker smoke tests or install dependencies from this module.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# Inspected against the repository's existing fixtures and CI definitions.
# Student 3's Docker-backed HTTP smoke tests are intentionally not run here.
SAFE_SUITES = {
    1: [
        ("staff-pytest", "pytest", "student-1-Andy-Lam/tests"),
    ],
    2: [
        ("allocation-endpoints", "pytest", "student-2Hein-Htet-Aung/tests/test_release2_endpoints.py"),
        ("allocation-backend", "unittest", "student-2Hein-Htet-Aung/tests/test_backend.py"),
        ("allocation-database", "unittest", "student-2Hein-Htet-Aung/tests/test_database.py"),
    ],
    3: [],
    4: [
        ("research-route-registration", "pytest", "student-4Nicholas-Hatzidimitriou/backend/tests/test_ai_mode_routes.py"),
    ],
    5: [
        ("performance-endpoints", "pytest", "student-5Matthew-Barnard/tests/test_release2_endpoints.py"),
        ("performance-backend", "unittest_discover", "student-5Matthew-Barnard/backend-service/tests"),
        ("performance-database", "unittest_discover", "student-5Matthew-Barnard/database-service/tests"),
    ],
}

# Maps workflow files to the owners whose CI result they represent.
WORKFLOWS = {
    1: "student-1-AndyLam.yml",
    2: "student-2-HeinHtetAung.yml",
    3: "student-3-TristanLim.yml",
    4: "student-4-NicholasHatzidimitriou.yml",
    5: "student-5-MatthewBarnard.yml",
}

REPOSITORY = "Hein-Htet-Aung08/faculty-management-system-ASD"


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _git(root, *args):
    try:
        completed = subprocess.run(
            ["git", *args], cwd=root, check=False,
            capture_output=True, text=True, timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() if completed.returncode == 0 else None


def _result_counts(kind, output, xml_path):
    if kind == "pytest" and xml_path.is_file():
        try:
            parsed = ET.parse(xml_path).getroot()
            suites = [parsed] if parsed.tag == "testsuite" else list(parsed.iter("testsuite"))
            # For a testsuites root, choose leaf suites to avoid double counts.
            leaves = [suite for suite in suites if not suite.findall("testsuite")]
            counts = {
                name: sum(int(s.attrib.get(name, 0)) for s in leaves)
                for name in ("tests", "failures", "errors", "skipped")
            }
            return counts
        except (ET.ParseError, ValueError):
            pass

    if kind.startswith("unittest"):
        match = re.search(r"\bRan (\d+) tests? in\b", output)
        if match:
            return {"tests": int(match.group(1))}

    return {"tests": None}


def suite_environment(base_env, student, suite_name, root):
    """Give each approved suite only the environment needed for its tests.

    Keep external integrations disabled by default. Student 5's backend
    unit suite mocks the AI generator, so its AI route flag must be enabled
    to exercise the expected 201 and 400 response paths. Student 4's route
    test imports `app` from its backend directory.
    """
    env = base_env.copy()

    if student == 4 and suite_name == "research-route-registration":
        backend = str(
            Path(root) / "student-4Nicholas-Hatzidimitriou" / "backend"
        )
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(
            part for part in (backend, existing) if part
        )

    if student == 5 and suite_name == "performance-backend":
        env["AI_MODE_ENABLED"] = "true"

    return env


def run_local_suites(repo_root, timeout_seconds=180):
    """Run allowlisted suites in separate subprocesses, returning metadata only.

    The raw stdout/stderr is stored under ignored reports/release2/live-tests.
    The caller must have explicitly selected fresh tests in the menu.
    """
    root = Path(repo_root).resolve()
    commit = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    dirty_state = _git(root, "status", "--porcelain", "--untracked-files=no")
    dirty = True if dirty_state is None else bool(dirty_state)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    report_dir = root / "reports" / "release2" / "live-tests" / stamp
    report_dir.mkdir(parents=True, exist_ok=False)

    results = {}
    with tempfile.TemporaryDirectory(prefix="agentic-safe-tests-") as isolated:
        scratch = Path(isolated)
        env = os.environ.copy()
        # Do not pass cloud/API credentials or a production DB URL to tests.
        private_prefixes = ("AWS_", "GITHUB_", "OPENAI_", "AZURE_", "GOOGLE_APPLICATION_")
        for key in list(env):
            if key.startswith(private_prefixes) or key in {
                "DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "DB_HOST", "DB_PASSWORD",
                "PGPASSWORD", "MONGO_URI", "MONGODB_URI",
            }:
                env.pop(key, None)
        env.update({
            "CI": "true",
            "TESTING": "true",
            "AI_MODE_ENABLED": "false",
            "MCP_ENABLED": "false",
            "RAG_ENABLED": "false",
            "MULTI_AGENT_ENABLED": "false",
            "OLLAMA_BASE_URL": "http://127.0.0.1:9/v1",
            "STUDENT1_BACKEND_URL": "http://127.0.0.1:9",
            "STUDENT2_BACKEND_URL": "http://127.0.0.1:9",
            "STUDENT3_BACKEND_URL": "http://127.0.0.1:9",
            "STUDENT4_BACKEND_URL": "http://127.0.0.1:9",
            "STUDENT5_BACKEND_URL": "http://127.0.0.1:9",
            "DB_PATH": str(scratch / "staff-isolated.db"),
            "DATABASE_PATH": str(scratch / "database-isolated.db"),
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        for student, suites in SAFE_SUITES.items():
            results[student] = []
            if not suites:
                continue

            for name, kind, target in suites:
                path = root / target
                if not path.exists():
                    results[student].append({
                        "suite": name, "status": "NOT_CONFIGURED",
                        "reason": f"Missing test path: {target}",
                    })
                    continue

                xml_path = report_dir / f"{name}.xml"
                if kind == "pytest":
                    command = [
                        sys.executable, "-m", "pytest", target,
                        "-q", "-ra", f"--junitxml={xml_path}",
                    ]
                elif kind == "unittest":
                    command = [
                        sys.executable, "-m", "unittest", "discover",
                        "-s", str(path.parent), "-p", path.name, "-v",
                    ]
                elif kind == "unittest_discover":
                    command = [
                        sys.executable, "-m", "unittest", "discover",
                        "-s", str(path), "-p", "test_*.py", "-v",
                    ]
                else:
                    raise ValueError("Unexpected allowlisted test type")

                print(f"[FRESH TESTS][Student {student}] {name}: running")
                try:
                    completed = subprocess.run(
                        command,
                        cwd=root,
                        env=suite_environment(env, student, name, root),
                        check=False,
                        capture_output=True, text=True,
                        timeout=timeout_seconds,
                    )
                    output = completed.stdout + "\n" + completed.stderr
                    count = _result_counts(kind, output, xml_path)
                    passed = completed.returncode == 0 and (
                        count.get("tests") is not None and count["tests"] > 0
                    )
                    status = "PASS" if passed else "FAIL_OR_ERROR"
                    exit_code = completed.returncode
                except subprocess.TimeoutExpired as exc:
                    output = (
                        (exc.stdout or b"").decode(errors="replace")
                        if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                    ) + "\nTIMEOUT: isolated test process exceeded allowed duration"
                    count = {"tests": None}
                    status, exit_code = "TIMEOUT", None
                except OSError as exc:
                    output = f"PROCESS ERROR: {type(exc).__name__}: {exc}"
                    count = {"tests": None}
                    status, exit_code = "ERROR", None

                log_path = report_dir / f"{name}.log"
                log_path.write_text(output, encoding="utf-8")
                results[student].append({
                    "suite": name, "status": status,
                    "test_count": count.get("tests"),
                    "failures": count.get("failures"),
                    "errors": count.get("errors"),
                    "skipped": count.get("skipped"),
                    "exit_code": exit_code,
                    "log": str(log_path.relative_to(root)),
                })
                print(f"[FRESH TESTS][Student {student}] {name}: {status}")

    summary = {
        "timestamp": _utc(), "commit": commit, "branch": branch,
        "local_tracked_changes": dirty, "students": results,
    }
    (report_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    summary["summary_path"] = str((report_dir / "summary.json").relative_to(root))
    return summary


def check_current_commit_ci(commit, timeout=8):
    """Read GitHub Actions runs at precisely this commit; no fallback to old runs."""
    statuses = {student: "CI_UNVERIFIED" for student in WORKFLOWS}
    if not commit or not re.fullmatch(r"[0-9a-f]{40}", commit):
        return statuses, "Local git commit SHA unavailable"

    query = urllib.parse.urlencode({"head_sha": commit, "per_page": 100})
    url = f"https://api.github.com/repos/{REPOSITORY}/actions/runs?{query}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "faculty-agentic-loop-readonly-ci-check",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.load(response)
        runs = payload.get("workflow_runs", [])
    except (OSError, ValueError, urllib.error.HTTPError) as exc:
        return statuses, f"CI API unavailable: {type(exc).__name__}"

    for student, filename in WORKFLOWS.items():
        matches = [
            run for run in runs
            if run.get("head_sha") == commit
            and str(run.get("path", "")).split("@")[0].endswith("/" + filename)
        ]
        if not matches:
            statuses[student] = "NO_CI_RUN_FOR_CURRENT_COMMIT"
            continue
        latest = max(matches, key=lambda item: item.get("run_number", 0))
        state = latest.get("status")
        conclusion = latest.get("conclusion")
        statuses[student] = (
            "SUCCESS_AT_COMMIT" if state == "completed" and conclusion == "success"
            else f"CI_{(conclusion or state or 'unknown').upper()}_AT_COMMIT"
        )
    return statuses, f"GitHub Actions queried for exact commit {commit[:12]}"
