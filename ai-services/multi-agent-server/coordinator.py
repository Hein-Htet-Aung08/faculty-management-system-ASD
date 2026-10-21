import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.planner_agent import plan_workflow
from agents.reviewer_agent import review_output
from agents.worker_agent import generate_output
from evidence import FEATURES, EvidenceError, collect_evidence, normalise_feature
from output_checks import check_worker_output, format_checks


BASE_DIR = Path(__file__).resolve().parent

# workflow_history.jsonl: one "workflow" event per run plus one "human_decision" event per decision.
# coordination_audit.jsonl: one line per coordination step, for the audit trail.
HISTORY_PATH = Path(os.getenv("MULTI_AGENT_HISTORY_PATH", BASE_DIR / "workflow_history.jsonl"))
AUDIT_PATH = Path(os.getenv("MULTI_AGENT_AUDIT_PATH", BASE_DIR / "coordination_audit.jsonl"))

MAX_REQUEST_CHARS = 1000
MAX_NOTE_CHARS = 2000
MAX_REVIEWER_CHARS = 100

PARTICIPATING_AGENTS = ["planner_agent", "worker_agent", "reviewer_agent", "human_reviewer"]

# Human review options from the Release 2 brief: approval, partial acceptance, correction or rejection.
DECISIONS = {
    "accept": ("Accept", "accepted"),
    "partially accept": ("Partially Accept", "partially_accepted"),
    "correct": ("Correct", "corrected"),
    "reject": ("Reject", "rejected"),
}
ALLOWED_DECISIONS = [label for label, _ in DECISIONS.values()]

_log_lock = threading.Lock()


class WorkflowNotFound(LookupError):
    pass


class DecisionConflict(Exception):
    pass


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path, record):
    with _log_lock:
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")


def read_jsonl(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def audit(workflow_id, feature, event, agent, status, started=None, **detail):
    record = {
        "timestamp": now_iso(),
        "workflow_id": workflow_id,
        "feature": feature,
        "event": event,
        "agent": agent,
        "status": status,
    }
    if started is not None:
        record["duration_ms"] = int((time.time() - started) * 1000)
    record.update(detail)
    append_jsonl(AUDIT_PATH, record)


def validate_request(user_request, feature):
    user_request = (user_request or "").strip()
    if not user_request:
        raise ValueError("user_request is required")
    if len(user_request) > MAX_REQUEST_CHARS:
        raise ValueError(f"user_request must be at most {MAX_REQUEST_CHARS} characters")

    feature_key = normalise_feature(feature)
    if feature_key is None:
        raise ValueError(f"feature must be one of: {', '.join(FEATURES)}")
    return user_request, feature_key


def run_workflow(user_request, feature):
    """Planner -> Worker -> Reviewer, then stop and wait for a human decision."""
    user_request, feature_key = validate_request(user_request, feature)
    meta = FEATURES[feature_key]
    workflow_id = str(uuid.uuid4())
    workflow_started = time.time()

    audit(workflow_id, feature_key, "workflow_started", "coordinator", "running", user_request=user_request)

    step = time.time()
    planner_result = plan_workflow(user_request, meta)
    audit(workflow_id, feature_key, "planner_completed", "planner_agent", planner_result["status"], step,
          model=planner_result["model"])

    step = time.time()
    try:
        evidence, available = collect_evidence(feature_key, user_request)
        evidence_error = None
    except EvidenceError as exc:
        evidence, available, evidence_error = [], 0, str(exc)
    audit(workflow_id, feature_key, "evidence_collected", "worker_agent",
          "error" if evidence_error else "success", step,
          evidence_count=len(evidence), evidence_available=available, error=evidence_error)

    step = time.time()
    worker_result = generate_output(user_request, meta, planner_result["plan"], evidence)
    if evidence_error:
        worker_result["evidence_error"] = evidence_error
    audit(workflow_id, feature_key, "worker_completed", "worker_agent", worker_result["status"], step,
          model=worker_result["model"], evidence_count=worker_result["evidence_count"])

    checks = check_worker_output(worker_result, evidence)
    failed = [c["check"] for c in checks if not c["passed"]]
    audit(workflow_id, feature_key, "automated_checks_completed", "coordinator",
          "failed" if failed else "passed", failed_checks=failed)

    step = time.time()
    reviewer_result = review_output(user_request, meta, planner_result["plan"], evidence, worker_result,
                                    format_checks(checks))
    audit(workflow_id, feature_key, "reviewer_completed", "reviewer_agent", reviewer_result["status"], step,
          model=reviewer_result["model"])

    workflow = {
        "event": "workflow",
        "workflow_id": workflow_id,
        "timestamp": now_iso(),
        "duration_ms": int((time.time() - workflow_started) * 1000),
        "feature": feature_key,
        "feature_name": meta["name"],
        "user_request": user_request,
        "status": "awaiting_human_review",
        "participating_agents": PARTICIPATING_AGENTS,
        "planner_result": planner_result,
        "evidence": evidence,
        "worker_result": worker_result,
        "automated_checks": checks,
        "reviewer_result": reviewer_result,
        "human_decision": {"required": True, "status": "pending", "allowed_values": ALLOWED_DECISIONS},
    }
    append_jsonl(HISTORY_PATH, workflow)
    audit(workflow_id, feature_key, "awaiting_human_review", "human_reviewer", "pending", workflow_started)
    return workflow


def _decisions_by_id(history):
    return {r["workflow_id"]: r for r in history if r.get("event") == "human_decision"}


def _merge(workflow, decision):
    if decision is None:
        return workflow
    merged = dict(workflow)
    merged["status"] = decision["outcome"]
    merged["human_decision"] = {"required": True, "status": "recorded", **decision}
    return merged


def get_workflow(workflow_id):
    history = read_jsonl(HISTORY_PATH)
    for record in history:
        if record.get("event") == "workflow" and record["workflow_id"] == workflow_id:
            return _merge(record, _decisions_by_id(history).get(workflow_id))
    raise WorkflowNotFound(workflow_id)


def record_decision(workflow_id, decision, reviewer=None, notes=None, correction=None):
    key = str(decision or "").strip().lower().replace("_", " ")
    if key not in DECISIONS:
        raise ValueError(f"decision must be one of: {', '.join(ALLOWED_DECISIONS)}")
    label, outcome = DECISIONS[key]

    reviewer = (reviewer or "").strip() or "Human Reviewer"
    notes = (notes or "").strip()
    correction = (correction or "").strip()
    if len(reviewer) > MAX_REVIEWER_CHARS:
        raise ValueError(f"reviewer must be at most {MAX_REVIEWER_CHARS} characters")
    if len(notes) > MAX_NOTE_CHARS or len(correction) > MAX_NOTE_CHARS:
        raise ValueError(f"notes and correction must be at most {MAX_NOTE_CHARS} characters")
    if label == "Correct" and not correction:
        raise ValueError("a correction is required when the decision is Correct")

    # Check-then-append under the lock so one workflow can only be decided once.
    with _log_lock:
        history = read_jsonl(HISTORY_PATH)
        workflow = next(
            (r for r in history if r.get("event") == "workflow" and r["workflow_id"] == workflow_id),
            None,
        )
        if workflow is None:
            raise WorkflowNotFound(workflow_id)
        if workflow_id in _decisions_by_id(history):
            raise DecisionConflict(f"workflow {workflow_id} already has a human decision")

        decision_record = {
            "event": "human_decision",
            "workflow_id": workflow_id,
            "timestamp": now_iso(),
            "feature": workflow["feature"],
            "decision": label,
            "outcome": outcome,
            "reviewer": reviewer,
            "notes": notes,
            "correction": correction,
        }
        with HISTORY_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(decision_record) + "\n")

    audit(workflow_id, workflow["feature"], "human_decision_recorded", "human_reviewer", outcome,
          decision=label, reviewer=reviewer)
    return _merge(workflow, decision_record)


def list_workflows(feature=None, limit=20):
    history = read_jsonl(HISTORY_PATH)
    decisions = _decisions_by_id(history)
    feature_key = normalise_feature(feature) if feature else None

    summaries = []
    for record in reversed(history):
        if record.get("event") != "workflow":
            continue
        if feature_key and record["feature"] != feature_key:
            continue
        merged = _merge(record, decisions.get(record["workflow_id"]))
        summaries.append({
            "workflow_id": record["workflow_id"],
            "timestamp": record["timestamp"],
            "feature": record["feature"],
            "user_request": record["user_request"],
            "status": merged["status"],
            "evidence_count": record["worker_result"]["evidence_count"],
            "decision": merged["human_decision"].get("decision"),
        })
        if len(summaries) >= limit:
            break
    return summaries


def workflow_status():
    history = read_jsonl(HISTORY_PATH)
    workflows = [r for r in history if r.get("event") == "workflow"]
    decisions = _decisions_by_id(history)

    by_decision = {}
    for decision in decisions.values():
        by_decision[decision["decision"]] = by_decision.get(decision["decision"], 0) + 1

    latest = None
    if workflows:
        latest = _merge(workflows[-1], decisions.get(workflows[-1]["workflow_id"]))

    return {
        "status": "success",
        "workflow_history_count": len(workflows),
        "human_decision_count": len(decisions),
        "pending_human_review": len(workflows) - len(decisions),
        "decisions": by_decision,
        "audit_record_count": len(read_jsonl(AUDIT_PATH)),
        "latest_workflow": latest,
    }
