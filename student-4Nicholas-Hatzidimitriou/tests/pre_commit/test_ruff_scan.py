import subprocess
import sys

STUDENT4_PATHS = [
    "student-4Nicholas-Hatzidimitriou/backend",
    "student-4Nicholas-Hatzidimitriou/database-service",
    "student-4Nicholas-Hatzidimitriou/frontend",
    "student-4Nicholas-Hatzidimitriou/tests",
]


def test_ruff_scan_passes():
    result = subprocess.run(  # noqa: S603 - fixed ruff invocation, not untrusted input
        [
            sys.executable, "-m", "ruff", "check",
            "--select", "S",
            "--per-file-ignores", "student-4Nicholas-Hatzidimitriou/**/tests/**:S101",
            "--output-format=concise",
            *STUDENT4_PATHS,
        ],
        capture_output=True,
        text=True,
    )
    returncode = result.returncode
    assert returncode == 0, result.stdout + result.stderr
