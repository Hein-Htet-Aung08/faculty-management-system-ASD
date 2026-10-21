import openai

from agents.llm_client import (
    REVIEW_MODEL,
    REVIEW_TIMEOUT_SECONDS,
    chat,
    env_int,
    load_prompt,
    parse_sections,
)
from agents.worker_agent import format_evidence


REVIEWER_MAX_TOKENS = env_int("REVIEWER_MAX_TOKENS", "250")
REVIEW_HEADINGS = ["Risk", "Correction", "Retest", "Recommendation"]


def review_output(user_request, feature, plan_text, evidence, worker_result, checks_text="None"):
    prompt = (
        f"Feature: {feature['name']}\n\n"
        f"User Request:\n{user_request}\n\n"
        f"Plan:\n{plan_text}\n\n"
        f"Evidence:\n{format_evidence(evidence) or 'None'}\n\n"
        f"Worker Output (status: {worker_result['status']}):\n{worker_result['output']}\n\n"
        f"Automated Checks:\n{checks_text}\n\n"
        f"{load_prompt('reviewer_prompt.txt')}"
    )

    try:
        review = chat(REVIEW_MODEL, prompt, max_tokens=REVIEWER_MAX_TOKENS, timeout=REVIEW_TIMEOUT_SECONDS)
        status, error = ("success", None) if review else ("error", "empty model response")
    except openai.APIError as exc:
        review, status, error = "", "error", str(exc)

    if status == "error":
        review = (
            "Risk: Review model unavailable, so the output is unreviewed.\n"
            "Correction: Check that Ollama is running and the review model is pulled.\n"
            "Retest: Run the workflow again.\n"
            f"Recommendation: Do not accept until reviewed. Error: {error}"
        )

    result = {
        "status": status,
        "agent": "reviewer_agent",
        "model": REVIEW_MODEL,
        "review": review,
        "sections": parse_sections(review, REVIEW_HEADINGS),
        "human_approval_required": True,
    }
    if error:
        result["error"] = error
    return result
