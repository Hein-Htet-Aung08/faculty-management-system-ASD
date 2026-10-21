import openai

from agents.llm_client import (
    AGENT_TIMEOUT_SECONDS,
    WORKER_MODEL,
    chat,
    env_int,
    load_prompt,
    parse_sections,
)


WORKER_MAX_TOKENS = env_int("WORKER_MAX_TOKENS", "300")
OUTPUT_HEADINGS = ["Output", "Evidence Used", "Limitations"]
MAX_RECORD_CHARS = 300


def format_evidence(evidence):
    """One line per item: '[source] key=value; key=value'."""
    lines = []
    for item in evidence:
        fields = "; ".join(f"{key}={value}" for key, value in item["record"].items())
        lines.append(f"[{item['source']}] {fields}"[:MAX_RECORD_CHARS])
    return "\n".join(lines)


def generate_output(user_request, feature, plan_text, evidence):
    base = {
        "agent": "worker_agent",
        "model": WORKER_MODEL,
        "evidence_count": len(evidence),
        "evidence_sources": [item["source"] for item in evidence],
        "human_approval_required": True,
    }

    # No evidence means nothing to ground an answer in, so the model is not called.
    if not evidence:
        output = (
            "Output:\nNo answer produced.\n\n"
            "Evidence Used:\nNone.\n\n"
            "Limitations:\nNo evidence was available from the feature backend."
        )
        return {**base, "status": "no_evidence", "output": output, "sections": parse_sections(output, OUTPUT_HEADINGS)}

    # Instructions go last: models follow the closest instruction most reliably.
    evidence_text = format_evidence(evidence)
    prompt = (
        f"Feature: {feature['name']}\n\n"
        f"Plan:\n{plan_text}\n\n"
        f"User Request:\n{user_request}\n\n"
        f"Evidence:\n{evidence_text}\n\n"
        f"{load_prompt('worker_prompt.txt')}\n\n"
        "Answer the User Request now. Start your reply with 'Output:'."
    )

    try:
        output = chat(WORKER_MODEL, prompt, max_tokens=WORKER_MAX_TOKENS, timeout=AGENT_TIMEOUT_SECONDS)
        status, error = ("success", None) if output else ("error", "empty model response")
    except openai.APIError as exc:
        output, status, error = "", "error", str(exc)

    if status == "error":
        output = (
            "Output:\nModel output could not be generated.\n\n"
            f"Evidence Used:\n{evidence_text}\n\n"
            f"Limitations:\nWorker model failed; human review required. Error: {error}"
        )

    result = {**base, "status": status, "output": output, "sections": parse_sections(output, OUTPUT_HEADINGS)}
    if error:
        result["error"] = error
    return result
