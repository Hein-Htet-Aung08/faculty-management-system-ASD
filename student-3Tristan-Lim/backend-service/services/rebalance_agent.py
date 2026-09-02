from services import llm_client
from services import prompt_loader

MAX_PROPOSALS = 3
MAX_CANDIDATES = 6


# ---------------------------------------------------------------------- plan ---

def _pick_source(analyses, staff_id=None):
    """The staff member to rebalance: the requested one, else the worst overload."""
    if staff_id:
        return next((a for a in analyses if str(a["staff_id"]) == str(staff_id)), None)

    overloaded = [a for a in analyses if a["status"] == "overloaded"]
    if not overloaded:
        return None
    return min(overloaded, key=lambda a: a["headroom"])


def _pick_candidates(analyses, source):
    """Staff with real headroom, same department first."""
    candidates = [
        a for a in analyses
        if a["staff_id"] != source["staff_id"]
        and a["status"] != "overloaded"
        and (a["headroom"] or 0) > 0
    ]
    candidates.sort(
        key=lambda a: (a["department"] != source["department"], -(a["headroom"] or 0))
    )
    return candidates[:MAX_CANDIDATES]


def build_plan(analyses, dataset, staff_id=None):
    source = _pick_source(analyses, staff_id)
    if source is None:
        return None

    entries = dataset.get(source["staff_id"], {}).get("entries", [])
    return {
        "source": source,
        "activities": sorted(entries, key=lambda e: -float(e.get("hours_per_week") or 0)),
        "candidates": _pick_candidates(analyses, source),
    }


def render_plan_context(plan):
    """The evidence block handed to the model. Numbers only, no interpretation."""
    source = plan["source"]

    activities = "\n".join(
        f"- {e.get('description')} | {e.get('activity_type')} | "
        f"{float(e.get('hours_per_week') or 0):.1f}h/week"
        for e in plan["activities"]
    ) or "- none recorded"

    candidates = "\n".join(
        f"- staff_id {c['staff_id']} | {c['staff_name']} | {c['department']} | "
        f"{c['computed_hours']:.1f}h of {c['cap']:.1f}h cap | headroom {c['headroom']:.1f}h"
        for c in plan["candidates"]
    ) or "- none available"

    clashes = "\n".join(f"- {c['detail']}" for c in source["clashes"]) or "- none detected"

    return f"""
SOURCE STAFF MEMBER
- staff_id: {source['staff_id']}
- name: {source['staff_name']}
- department: {source['department']}
- hours: {source['computed_hours']:.1f}
- cap: {source['cap']:.1f}
- headroom: {source['headroom']:.1f}

ACTIVITIES
{activities}

CANDIDATES
{candidates}

CLASHES
{clashes}
""".strip()


# ----------------------------------------------------------------------- act ---

def _build_user_prompt(plan, feedback=None):
    task = prompt_loader.load_service_prompt("rebalance_task_prompt.txt")
    context_notes = prompt_loader.load_service_prompt("context_prompt.txt")
    sections = [task, context_notes, render_plan_context(plan)]

    if feedback:
        review = prompt_loader.load_service_prompt("rebalance_review_prompt.txt")
        sections += [review, feedback]

    return "\n\n".join(sections)


def act(plan, feedback=None, model=None):
    """Ask the model for proposals. Returns (raw_text, proposals)."""
    system_prompt = prompt_loader.load_service_prompt("system_prompt.txt")
    raw = llm_client.ask(
        system_prompt,
        _build_user_prompt(plan, feedback),
        max_tokens=800,
        temperature=0.2,
        model=model,
    )

    parsed = llm_client.extract_json(raw)
    proposals = []
    if isinstance(parsed, dict):
        proposals = parsed.get("proposals") or []
    if not isinstance(proposals, list):
        proposals = []

    return raw, proposals[:MAX_PROPOSALS]


# ------------------------------------------------------------------- observe ---

def _match_activity(name, activities):
    """Match a model-supplied activity description to a real workload entry."""
    if not name:
        return None
    wanted = str(name).strip().lower()

    for entry in activities:
        if str(entry.get("description") or "").strip().lower() == wanted:
            return entry

    # Models often shorten a description to just the subject code or title.
    for entry in activities:
        description = str(entry.get("description") or "").strip().lower()
        if description and (wanted in description or description in wanted):
            return entry
    return None


def observe(plan, proposals):
    """Validate each proposal against live figures. The model is not trusted."""
    source = plan["source"]
    candidates = {c["staff_id"]: c for c in plan["candidates"]}
    observations = []

    # Track hours already committed to each target within this proposal set, so
    # three proposals cannot each spend the same headroom.
    committed = {}

    for proposal in proposals:
        if not isinstance(proposal, dict):
            observations.append({"proposal": proposal, "verdict": "rejected",
                                 "reason": "malformed proposal"})
            continue

        activity = _match_activity(proposal.get("activity"), plan["activities"])
        record = {
            "proposal": proposal,
            "activity": activity.get("description") if activity else proposal.get("activity"),
            "entry_id": activity.get("entry_id") if activity else None,
        }

        if activity is None:
            observations.append({**record, "verdict": "rejected",
                                 "reason": "activity does not exist for this staff member"})
            continue

        try:
            hours = float(proposal.get("hours"))
        except (TypeError, ValueError):
            observations.append({**record, "verdict": "rejected",
                                 "reason": "hours is not a number"})
            continue

        available = float(activity.get("hours_per_week") or 0)
        if hours <= 0:
            observations.append({**record, "verdict": "rejected",
                                 "reason": "hours must be greater than zero"})
            continue
        if hours > available:
            observations.append({**record, "verdict": "rejected",
                                 "reason": f"activity is only {available:.1f}h, cannot move {hours:.1f}h"})
            continue

        record["hours"] = hours
        record["source_after"] = round(source["computed_hours"] - hours, 2)
        record["source_within_cap"] = record["source_after"] <= source["cap"]

        target_id = proposal.get("to_staff_id")

        # A null target means defer or drop the work rather than reassign it.
        if target_id in (None, "", "null"):
            observations.append({**record, "verdict": "accepted", "target": None,
                                 "reason": "work deferred or reduced rather than reassigned"})
            continue

        try:
            target_id = int(target_id)
        except (TypeError, ValueError):
            observations.append({**record, "verdict": "rejected",
                                 "reason": "to_staff_id is not a valid staff id"})
            continue

        target = candidates.get(target_id)
        if target is None:
            observations.append({**record, "verdict": "rejected",
                                 "reason": f"staff {target_id} is not an eligible candidate"})
            continue

        already = committed.get(target_id, 0)
        target_after = round(target["computed_hours"] + already + hours, 2)
        record.update({
            "target": target_id,
            "target_name": target["staff_name"],
            "target_after": target_after,
            "target_cap": target["cap"],
        })

        if target_after > target["cap"]:
            observations.append({**record, "verdict": "rejected",
                                 "reason": (f"{target['staff_name']} would reach {target_after:.1f}h, "
                                            f"over their {target['cap']:.1f}h cap")})
            continue

        committed[target_id] = already + hours
        observations.append({**record, "verdict": "accepted",
                             "reason": (f"{target['staff_name']} moves to {target_after:.1f}h "
                                        f"of {target['cap']:.1f}h")})

    return observations


def render_feedback(observations):
    """Validation results, formatted for the Adapt round."""
    lines = []
    for observation in observations:
        proposal = observation.get("proposal") or {}
        lines.append(
            f"- {observation['verdict'].upper()}: move "
            f"{proposal.get('hours')}h of '{observation.get('activity')}' "
            f"to staff {proposal.get('to_staff_id')} -- {observation['reason']}"
        )
    return "VALIDATION RESULTS\n" + "\n".join(lines)


# --------------------------------------------------------------------- cycle ---

def run_cycle(analyses, dataset, staff_id=None, max_rounds=2, model=None):
    """Run Plan -> Act -> Observe, adapting once if any proposal fails."""
    plan = build_plan(analyses, dataset, staff_id)
    if plan is None:
        return None

    rounds = []
    feedback = None

    for round_number in range(1, max_rounds + 1):
        raw, proposals = act(plan, feedback=feedback, model=model)
        observations = observe(plan, proposals)
        rounds.append({
            "round": round_number,
            "phase": "act" if round_number == 1 else "adapt",
            "raw": raw,
            "proposals": proposals,
            "observations": observations,
        })

        rejected = [o for o in observations if o["verdict"] == "rejected"]
        if not proposals or not rejected or round_number == max_rounds:
            break
        feedback = render_feedback(observations)

    final = rounds[-1]["observations"]
    return {
        "plan": plan,
        "context": render_plan_context(plan),
        "rounds": rounds,
        "accepted": [o for o in final if o["verdict"] == "accepted"],
        "rejected": [o for o in final if o["verdict"] == "rejected"],
        "model": model or llm_client.OLLAMA_MODEL,
    }


def to_recommendation_rows(cycle):
    """Accepted observations as rebalance_recommendation rows awaiting review."""
    source = cycle["plan"]["source"]
    rows = []

    for observation in cycle["accepted"]:
        hours = observation.get("hours")
        target = observation.get("target")
        if target is None:
            action = f"Defer or reduce '{observation['activity']}' ({hours:.1f}h)"
        else:
            action = (f"Move '{observation['activity']}' ({hours:.1f}h) to "
                      f"{observation.get('target_name')}")

        rows.append({
            "staff_id": source["staff_id"],
            "suggested_action": action,
            "target_staff_id": target,
            "rationale": f"{observation['reason']} (proposed by {cycle['model']})",
            "decision_status": "pending",
        })

    return rows
