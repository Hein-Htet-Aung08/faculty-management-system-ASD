import requests
from flask import Blueprint, request

from routes.workload_ui import _analyse_all, _load_workload_dataset
from services import database_api as db
from services import llm_client
from services import prompt_loader
from services import rebalance_agent
from services import workload_rules as rules
from views import ai_formatters as fmt_ai
from views import html_formatters as fmt

ai_mode_bp = Blueprint("ai_mode", __name__, url_prefix="/ai")

DECISIONS = ("accepted", "rejected", "overridden")


@ai_mode_bp.get("/health")
def health():
    """Confirm the LLM runtime is reachable and report the configured model."""
    try:
        llm_client.ask("You are a health check.", "Reply with the single word OK.",
                       max_tokens=5)
    except Exception as exc:
        return fmt.message(
            f"LLM unreachable at {llm_client.OLLAMA_BASE_URL}: {exc}", "error"
        ), 503

    return fmt.message(
        f"AI-Mode ready - {llm_client.OLLAMA_MODEL} via {llm_client.OLLAMA_BASE_URL}",
        "info",
    ), 200


@ai_mode_bp.post("/ask")
def ask():
    """Free-text question grounded in the current workload figures."""
    question = request.form.get("question", "").strip()
    if not question:
        return fmt.message("Question is required.", "warn"), 400

    try:
        analyses = _analyse_all()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    summary = "\n".join(
        f"- staff {a['staff_id']} | {a['staff_name']} | {a['department']} | "
        f"{a['computed_hours']:.1f}h of {a['cap']:.1f}h | {a['status']} | "
        f"{len(a['clashes'])} clash(es)"
        for a in sorted(analyses, key=lambda a: a["staff_id"])
    )

    try:
        system_prompt = prompt_loader.load_service_prompt("system_prompt.txt")
        answer = llm_client.ask(
            system_prompt,
            f"CURRENT WORKLOAD\n{summary}\n\nQUESTION\n{question}\n\n"
            "Answer in plain prose, not JSON. Use only the figures above.",
            max_tokens=400,
        )
    except Exception as exc:
        return fmt.message(f"AI request failed: {exc}", "error"), 503

    return fmt_ai.format_answer(question, answer, llm_client.OLLAMA_MODEL), 200


@ai_mode_bp.post("/rebalance")
def rebalance():
    """Run the full Plan -> Act -> Observe -> Adapt cycle for one staff member."""
    staff_id = request.form.get("staff_id", "").strip() or None
    persist = request.form.get("persist", "").strip() in ("1", "true", "on", "yes")

    try:
        dataset, rule_rows = _load_workload_dataset()
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    analyses = [
        rules.analyse_staff(b["profile"], b["entries"], b["slots"], b["leave"], rule_rows)
        for b in dataset.values()
    ]

    try:
        cycle = rebalance_agent.run_cycle(analyses, dataset, staff_id=staff_id)
    except Exception as exc:
        return fmt.message(f"AI request failed: {exc}", "error"), 503

    if cycle is None:
        return fmt.message(
            "No overloaded staff member to rebalance." if not staff_id
            else f"No workload profile for staff_id {staff_id}.", "warn"
        ), 404

    saved = []
    if persist:
        for row in rebalance_agent.to_recommendation_rows(cycle):
            try:
                response = db.create_row("rebalance_recommendation", row)
                if response.status_code < 400:
                    saved.append(response.json())
            except requests.RequestException:
                continue

    return fmt_ai.format_cycle(cycle, saved), 200


@ai_mode_bp.post("/recommendations/<int:rec_id>/decision")
def decide(rec_id):
    """Human review of an AI recommendation: accept, reject or override."""
    decision = request.form.get("decision", "").strip().lower()
    if decision not in DECISIONS:
        return fmt.message(f"decision must be one of {', '.join(DECISIONS)}.", "warn"), 400

    payload = {"decision_status": decision}
    override = request.form.get("suggested_action", "").strip()
    if decision == "overridden" and override:
        payload["suggested_action"] = override

    try:
        response = db.update_row("rebalance_recommendation", rec_id, payload)
        if response.status_code == 404:
            return fmt.message("Recommendation not found.", "warn"), 404
        if response.status_code >= 400:
            return fmt.message(f"update failed: {response.text}", "error"), response.status_code
        rows = db.list_rows("rebalance_recommendation")
    except requests.RequestException as exc:
        return fmt.message(f"database-service unreachable: {exc}", "error"), 503

    return fmt.format_recommendations(rows), 200
