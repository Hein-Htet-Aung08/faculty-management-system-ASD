import openai

from agents.llm_client import (
    AGENT_TIMEOUT_SECONDS,
    PLANNER_MODEL,
    chat,
    env_int,
    load_prompt,
    parse_sections,
)


PLANNER_MAX_TOKENS = env_int("PLANNER_MAX_TOKENS", "200")
PLAN_HEADINGS = ["Objective", "Steps", "Evidence Required", "Human Approval"]


def default_steps():
    return [
        {"step": 1, "agent": "planner_agent", "action": "Create the workflow plan"},
        {"step": 2, "agent": "worker_agent", "action": "Collect feature evidence and produce the output"},
        {"step": 3, "agent": "reviewer_agent", "action": "Review the output for risk, correction, retest and recommendation"},
        {"step": 4, "agent": "human_reviewer", "action": "Accept, partially accept, correct or reject"},
    ]


def fallback_plan(feature, reason):
    return (
        f"Objective: Answer the request using {feature['name']} evidence.\n"
        "Steps: 1. Collect evidence. 2. Produce output. 3. Review. 4. Human decision.\n"
        f"Evidence Required: {feature['evidence_description']}.\n"
        "Human Approval: Required.\n"
        f"Fallback Reason: {reason}"
    )


def plan_workflow(user_request, feature):
    prompt = (
        f"{load_prompt('planner_prompt.txt')}\n\n"
        f"Feature: {feature['name']}\n"
        f"Available Evidence: {feature['evidence_description']}\n\n"
        f"User Request:\n{user_request}\n"
    )

    try:
        plan = chat(PLANNER_MODEL, prompt, max_tokens=PLANNER_MAX_TOKENS, timeout=AGENT_TIMEOUT_SECONDS)
        status = "success" if plan else "fallback"
        error = None if plan else "empty model response"
    except openai.APIError as exc:
        plan, status, error = "", "fallback", str(exc)

    if status == "fallback":
        plan = fallback_plan(feature, error)

    result = {
        "status": status,
        "agent": "planner_agent",
        "model": PLANNER_MODEL,
        "plan": plan,
        "sections": parse_sections(plan, PLAN_HEADINGS),
        "steps": default_steps(),
        "human_approval_required": True,
    }
    if error:
        result["error"] = error
    return result
