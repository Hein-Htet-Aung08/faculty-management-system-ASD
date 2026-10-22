import subprocess
import sys
from pathlib import Path

STUDENT4_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = STUDENT4_ROOT.parent

REQUIREMENTS_FILES = [
    STUDENT4_ROOT / "backend" / "requirements.txt",
    STUDENT4_ROOT / "database-service" / "requirements.txt",
    STUDENT4_ROOT / "frontend" / "requirements.txt",
]


def test_pip_audit_passes():
    failures = []
    for req_file in REQUIREMENTS_FILES:
        result = subprocess.run(  # noqa: S603 - fixed pip-audit invocation over a known file path, not untrusted input
            [sys.executable, "-m", "pip_audit", "-r", str(req_file)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(f"{req_file.relative_to(REPO_ROOT)}:\n{result.stdout}{result.stderr}")

    assert not failures, "\n\n".join(failures)
