"""Read-only evidence collection for the Release 2 Cloud Deployment Review.

Evidence comes from three places, all optional except the manifest:

1. reports/cloud-deployment/deployment-evidence.json -- filled in by whoever
   deploys (platform, deployed commit, workflow run, per-student URLs).
   See reports/cloud-deployment/README.md for the format.
2. The repository itself -- cloud-deployment.yml, the deployment scripts and
   the cloud configuration named in the manifest.
3. Live HTTP probes of the deployed URLs, only when
   AGENTIC_CLOUD_PROBE_MODE=live (opt-in; GET requests only).

Nothing is deployed, changed or restarted by this collector. A successful
collection is not release approval: the final release decision is human.
"""

import json
import os
import re
from pathlib import Path

import requests


EVIDENCE_DIR = Path("reports") / "cloud-deployment"
MANIFEST_NAME = "deployment-evidence.json"
DECISION_NAME = "release-decision.json"
WORKFLOW_FILE = Path(".github") / "workflows" / "cloud-deployment.yml"

STUDENTS = (1, 2, 3, 4, 5)
SUPPORTED_PLATFORMS = {"aws", "azure"}

# AI features that must be OFF in the baseline cloud deployment.
AI_FLAGS = ("AI_MODE_ENABLED", "MCP_ENABLED", "RAG_ENABLED", "MULTI_AGENT_ENABLED")
AI_FLAG_PATTERN = re.compile(
    r"\b(" + "|".join(AI_FLAGS) + r")\b\s*[:=]\s*[\"']?(\w+)", re.IGNORECASE
)
# Status JSON keys such as "mcp_enabled": true from a backend status route.
AI_STATUS_KEYS = ("ai_mode_enabled", "mcp_enabled", "rag_enabled", "multi_agent_enabled")

# Credentials must never be committed alongside deployment files.
SECRET_PATTERNS = {
    "AWS access key ID": re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    "AWS secret access key": re.compile(
        r"aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+]{40}", re.IGNORECASE
    ),
    "private key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

try:
    PROBE_TIMEOUT_SECONDS = float(os.getenv("AGENTIC_CLOUD_PROBE_TIMEOUT", "10"))
except ValueError:
    PROBE_TIMEOUT_SECONDS = 10.0


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def load_manifest(path):
    """Return (manifest, error). The manifest must be a JSON object."""
    try:
        data = json.loads(read_text(path))
    except (OSError, ValueError) as exc:
        return None, f"{path.name} could not be read: {exc}"
    if not isinstance(data, dict):
        return None, f"{path.name} must contain a JSON object"
    return data, None


def check_workflow_file(root):
    """cloud-deployment.yml must exist and only deploy after CI succeeds."""
    path = root / WORKFLOW_FILE
    if not path.is_file():
        return "MISSING", f"{WORKFLOW_FILE.as_posix()} not found"

    text = read_text(path)
    gated_on_ci = (
        ("workflow_run" in text and "success" in text)
        or re.search(r"^\s*needs\s*:", text, re.MULTILINE) is not None
    )
    if not gated_on_ci:
        return "NOT_GATED", "workflow does not appear to wait for CI validation (no workflow_run success check or needs:)"
    return "PRESENT", "present and gated on CI validation"


def check_workflow_run(manifest, evidence_dir):
    """The manifest must record a successful cloud-deployment.yml run."""
    run = manifest.get("workflow_run")
    if not isinstance(run, dict):
        return "MISSING", "no workflow_run recorded in the manifest"

    conclusion = str(run.get("conclusion", "")).lower()
    url = run.get("url") or "no URL recorded"
    log_name = run.get("log")
    log_note = "no saved log"

    if log_name:
        log_path = evidence_dir / log_name
        if not log_path.is_file():
            return "INCOMPLETE", f"saved log {log_name} not found ({url})"
        log_note = f"saved log {log_name} ({len(read_text(log_path).splitlines())} lines)"

    if conclusion != "success":
        return "FAILED", f"conclusion={conclusion or 'unknown'} ({url})"
    if not log_name:
        return "INCOMPLETE", f"success recorded but {log_note} ({url})"
    return "SUCCESS_RECORDED", f"success, {log_note} ({url})"


def check_listed_files(root, paths, label):
    """Every file named in the manifest must exist in the repository."""
    if not isinstance(paths, list) or not paths:
        return "MISSING", f"no {label} listed in the manifest", []

    missing = [p for p in paths if not (root / p).is_file()]
    if missing:
        return "MISSING", f"not found in repo: {', '.join(missing)}", []
    return "PRESENT", ", ".join(paths), [root / p for p in paths]


def check_ai_disabled(config_files):
    """No AI feature flag may be set to true in the cloud configuration."""
    enabled = []
    seen = set()
    for path in config_files:
        for flag, value in AI_FLAG_PATTERN.findall(read_text(path)):
            seen.add(flag.upper())
            if value.lower() in {"true", "1", "yes", "on"}:
                enabled.append(f"{flag.upper()}={value} in {path.name}")

    if enabled:
        return "AI_ENABLED", "; ".join(enabled)
    if not seen:
        return "UNVERIFIED", "no AI feature flags found; code defaults are relied on"
    return "DISABLED", f"flags set off: {', '.join(sorted(seen))}"


def scan_for_secrets(files):
    found = []
    for path in files:
        text = read_text(path)
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                found.append(f"{name} in {path.name}")
    return ("FOUND", "; ".join(found)) if found else ("NONE_FOUND", "no credential patterns found")


def probe(url):
    """GET a deployed URL. Returns (status, detail, json_body_or_None)."""
    try:
        response = requests.get(url, timeout=PROBE_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        return "UNREACHABLE", f"{url}: {type(exc).__name__}", None

    body = None
    try:
        body = response.json()
    except ValueError:
        pass

    status = "OK" if response.status_code < 400 else "HTTP_ERROR"
    return status, f"{url}: HTTP {response.status_code}", body


def _join_url(base, path):
    return f"{str(base).rstrip('/')}/{str(path).lstrip('/')}"


def check_service(entry, live):
    """Deterministic + optional live checks for one student's deployed service."""
    findings = []
    row = {
        "frontend": "NOT_RECORDED",
        "backend": "NOT_RECORDED",
        "crud_read": "NOT_RECORDED",
        "ai_status": "NOT_RECORDED",
        "details": [],
    }

    frontend = entry.get("frontend_url")
    backend = entry.get("backend_url")
    crud_path = entry.get("crud_read_path")
    status_path = entry.get("ai_status_path")

    if not frontend:
        findings.append("frontend_url not recorded")
    if not backend:
        findings.append("backend_url not recorded")
    if not crud_path:
        findings.append("crud_read_path not recorded")

    if not live:
        for key, value in (("frontend", frontend), ("backend", backend), ("crud_read", crud_path)):
            if value:
                row[key] = "RECORDED_NOT_PROBED"
        if status_path:
            row["ai_status"] = "RECORDED_NOT_PROBED"
        row["findings"] = findings
        return row

    if frontend:
        row["frontend"], detail, _ = probe(frontend)
        row["details"].append(f"frontend {detail}")
    if backend and crud_path:
        row["crud_read"], detail, _ = probe(_join_url(backend, crud_path))
        row["backend"] = row["crud_read"]
        row["details"].append(f"CRUD read {detail}")
    if backend and status_path:
        status, detail, body = probe(_join_url(backend, status_path))
        row["details"].append(f"AI status {detail}")
        if status != "OK" or not isinstance(body, dict):
            row["ai_status"] = "UNVERIFIED"
        else:
            enabled = [key for key in AI_STATUS_KEYS if body.get(key) is True]
            row["ai_status"] = "AI_ENABLED" if enabled else "DISABLED"
            if enabled:
                findings.append("AI enabled in cloud: " + ", ".join(enabled))

    for key in ("frontend", "crud_read"):
        if row[key] in {"UNREACHABLE", "HTTP_ERROR"}:
            findings.append(f"{key} probe {row[key]}")

    row["findings"] = findings
    return row


RELEASE_DECISIONS = ("Release", "Release with conditions", "Do not release")


def write_release_decision(repo_root, decision, reviewer, notes, review_report):
    """
    Record the final human release decision next to the manifest. This is the
    only file the Cloud Deployment Review writes into the evidence folder, and
    only after a person has chosen a decision at the prompt.
    """
    if decision not in RELEASE_DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(RELEASE_DECISIONS)}")

    from datetime import datetime, timezone

    record = {
        "decision": decision,
        "reviewer": reviewer.strip() or "Human Reviewer",
        "notes": notes.strip(),
        "review_report": str(review_report),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path = Path(repo_root) / EVIDENCE_DIR / DECISION_NAME
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def load_decision(evidence_dir):
    path = evidence_dir / DECISION_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(read_text(path))
    except ValueError:
        return {"decision": "UNREADABLE"}
    return data if isinstance(data, dict) else {"decision": "UNREADABLE"}


def collect(app_dir, repo_root):
    """Return (collected, evidence_text); a successful collection is not approval."""
    root = Path(repo_root).resolve()
    evidence_dir = root / EVIDENCE_DIR
    manifest_path = evidence_dir / MANIFEST_NAME

    mode = os.getenv("AGENTIC_CLOUD_PROBE_MODE", "saved").strip().lower()
    if mode not in {"saved", "live"}:
        return False, "OBSERVE FAILED: unknown cloud probe mode"
    live = mode == "live"

    if not manifest_path.is_file():
        return False, (
            "OBSERVE FAILED: no cloud deployment evidence found.\n"
            f"Expected {EVIDENCE_DIR.as_posix()}/{MANIFEST_NAME} "
            f"(format: {EVIDENCE_DIR.as_posix()}/README.md). "
            "Deploy first, then record the deployment."
        )

    manifest, error = load_manifest(manifest_path)
    if error:
        return False, f"OBSERVE FAILED: {error}"

    blockers = []

    platform = str(manifest.get("platform", "")).strip()
    if platform.lower() not in SUPPORTED_PLATFORMS:
        blockers.append(f"platform must be AWS or Azure (got {platform or 'none'})")

    workflow_status, workflow_detail = check_workflow_file(root)
    if workflow_status != "PRESENT":
        blockers.append(f"cloud-deployment.yml {workflow_status}")

    run_status, run_detail = check_workflow_run(manifest, evidence_dir)
    if run_status != "SUCCESS_RECORDED":
        blockers.append(f"deployment run {run_status}")

    scripts_status, scripts_detail, script_files = check_listed_files(
        root, manifest.get("deployment_scripts"), "deployment_scripts"
    )
    if scripts_status != "PRESENT":
        blockers.append("deployment scripts MISSING")

    config_status, config_detail, config_files = check_listed_files(
        root, manifest.get("cloud_config"), "cloud_config"
    )
    ai_status, ai_detail = ("UNVERIFIED", "no cloud configuration to inspect")
    if config_files:
        ai_status, ai_detail = check_ai_disabled(config_files)
    if ai_status == "AI_ENABLED":
        blockers.append("AI enabled in cloud configuration")

    secrets_status, secrets_detail = scan_for_secrets(
        script_files + config_files + ([root / WORKFLOW_FILE] if (root / WORKFLOW_FILE).is_file() else [])
    )
    if secrets_status == "FOUND":
        blockers.append("credentials committed in deployment files")

    services = manifest.get("services")
    entries = {}
    if isinstance(services, list):
        for entry in services:
            if isinstance(entry, dict) and entry.get("student") in STUDENTS:
                entries[entry["student"]] = entry

    service_rows = {}
    for number in STUDENTS:
        if number not in entries:
            service_rows[number] = {"missing": True}
            blockers.append(f"Student {number} service not recorded")
            continue
        row = check_service(entries[number], live)
        service_rows[number] = row
        if row["findings"]:
            blockers.append(f"Student {number}: " + "; ".join(row["findings"]))

    if not live:
        # Saved evidence alone cannot show the deployed app is reachable
        blockers.append("deployed URLs not probed (run the review in live mode)")

    decision = load_decision(evidence_dir)
    decision_line = (
        "PENDING (no human release decision recorded yet)"
        if decision is None
        else f"{decision.get('decision', 'UNKNOWN')} by {decision.get('reviewer', 'unknown')} "
        f"at {decision.get('timestamp', 'unknown time')}"
    )

    verdict = "NOT_READY" if blockers else "HUMAN_VALIDATION_REQUIRED"

    lines = [
        f"DETERMINISTIC RELEASE VERDICT: {verdict}",
        "This verdict is authoritative. AI assessments are advisory only.",
        "",
        "CLOUD DEPLOYMENT REVIEW EVIDENCE",
        "Collection method: read-only manifest and repository inspection"
        + (" + live GET probes" if live else " (deployed URLs not probed)"),
        f"Manifest: {manifest_path.relative_to(root).as_posix()}",
        f"Platform: {platform or 'not recorded'} | Region: {manifest.get('region', 'not recorded')} "
        f"| Hosting: {manifest.get('hosting', 'not recorded')}",
        f"Deployed commit: {manifest.get('deployed_commit', 'not recorded')} "
        f"| Deployed at: {manifest.get('deployed_at', 'not recorded')}",
        f"cloud-deployment.yml: {workflow_status} - {workflow_detail}",
        f"Deployment run: {run_status} - {run_detail}",
        f"Deployment scripts: {scripts_status} - {scripts_detail}",
        f"Cloud configuration: {config_status} - {config_detail}",
        f"AI features in cloud config: {ai_status} - {ai_detail}",
        f"Credential scan of deployment files: {secrets_status} - {secrets_detail}",
        "",
    ]

    for number in STUDENTS:
        row = service_rows[number]
        if row.get("missing"):
            lines.append(f"Student {number}: NOT_RECORDED in manifest")
            continue
        lines.append(
            f"Student {number}: frontend={row['frontend']} backend={row['backend']} "
            f"crud_read={row['crud_read']} ai_status={row['ai_status']}"
        )
        for detail in row["details"]:
            lines.append(f"  - {detail}")
        lines.append(f"  Findings: {row['findings'] or ['None identified']}")

    lines.extend([
        "",
        f"Release blockers: {blockers or ['None identified']}",
        f"Human release decision: {decision_line}",
        "Note: evidence collection does not equal release approval.",
    ])

    return True, "\n".join(lines)
