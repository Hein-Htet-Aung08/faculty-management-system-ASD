import json
import subprocess
import sys
from pathlib import Path

STUDENT4_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = STUDENT4_ROOT.parent
BASELINE_PATH = REPO_ROOT / ".secrets.baseline"


def test_detect_secrets_scan_passes():
    result = subprocess.run(  # noqa: S603 - fixed detect-secrets invocation, not untrusted input
        [
            sys.executable, "-m", "detect_secrets", "scan",
            str(STUDENT4_ROOT.relative_to(REPO_ROOT)),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    returncode = result.returncode
    assert returncode == 0, result.stdout + result.stderr

    current = json.loads(result.stdout)
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    audited_hashes = {
        (filename, entry["hashed_secret"])
        for filename, entries in baseline.get("results", {}).items()
        for entry in entries
        if entry.get("is_secret") is False
    }

    unaudited = {}
    for filename, entries in current.get("results", {}).items():
        new_entries = [
            entry for entry in entries
            if (filename, entry["hashed_secret"]) not in audited_hashes
        ]
        if new_entries:
            unaudited[filename] = new_entries

    assert not unaudited, f"Unaudited potential secrets detected: {unaudited}"
