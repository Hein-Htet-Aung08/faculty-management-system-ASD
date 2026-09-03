import json
import os
from datetime import date

from openai import OpenAI

import database_client
from prompt_loader import load_prompt

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1"
).rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama", timeout=LLM_TIMEOUT)
RECOMMENDATION_TYPES = {"Training", "Goal", "Mentoring", "Experience"}


def _extract_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model response did not contain a JSON object")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError("model response contained invalid JSON") from exc


def _list(resource, **filters):
    response = database_client.list_resource(
        resource,
        {key: value for key, value in filters.items() if value not in (None, "")},
    )
    return database_client.read_json(response)


def build_staff_context(staff_id):
    reviews = _list("performance-reviews", staffID=staff_id)
    goals = _list("development-goals", staffID=staff_id)
    enrolments = _list("staff-training", staffID=staff_id)
    programs = _list("training-programs")

    if not reviews and not goals:
        raise ValueError("no performance reviews or development goals exist for this staff member")

    enrolled_ids = {row["trainingID"] for row in enrolments}
    return {
        "staffID": staff_id,
        "performanceReviews": reviews,
        "developmentGoals": goals,
        "currentTraining": [
            program for program in programs if program["trainingID"] in enrolled_ids
        ],
        "availableTrainingPrograms": programs,
    }


def _validate_recommendation(proposal, context):
    required = {"goalID", "recommendationType", "recommendation", "rationale"}
    if not isinstance(proposal, dict) or not required.issubset(proposal):
        raise ValueError("model response is missing required recommendation fields")

    recommendation_type = proposal["recommendationType"]
    if recommendation_type not in RECOMMENDATION_TYPES:
        raise ValueError("model returned an unsupported recommendation type")

    goal_id = proposal["goalID"]
    valid_goal_ids = {goal["goalID"] for goal in context["developmentGoals"]}
    if goal_id is not None:
        try:
            goal_id = int(goal_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("model returned an invalid goal ID") from exc
        if goal_id not in valid_goal_ids:
            raise ValueError("model referenced a goal that does not belong to this staff member")

    recommendation = str(proposal["recommendation"]).strip()
    rationale = str(proposal["rationale"]).strip()
    if not recommendation or not rationale:
        raise ValueError("model returned an empty recommendation or rationale")

    if recommendation_type == "Training":
        valid_titles = {
            program["title"] for program in context["availableTrainingPrograms"]
        }
        if not any(title.lower() in recommendation.lower() for title in valid_titles):
            raise ValueError("model recommended training that is not in the catalogue")

    return {
        "staffID": context["staffID"],
        "goalID": goal_id,
        "recommendationType": recommendation_type,
        "recommendation": recommendation,
        "rationale": rationale,
        "dateGenerated": date.today().isoformat(),
        "status": "Pending",
    }


def generate_recommendation(staff_id):
    context = build_staff_context(staff_id)
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": load_prompt("development_system_prompt.txt")},
            {
                "role": "user",
                "content": (
                    load_prompt("development_task_prompt.txt")
                    + "\n\nSUPPLIED RECORDS\n"
                    + json.dumps(context, indent=2)
                ),
            },
        ],
        temperature=0.2,
        max_tokens=350,
    )
    raw = response.choices[0].message.content or ""
    recommendation = _validate_recommendation(_extract_json(raw), context)
    saved_response = database_client.create_resource(
        "development-recommendations", recommendation
    )
    saved = database_client.read_json(saved_response)
    return {
        "mode": "single-pass-ai",
        "model": OLLAMA_MODEL,
        "recommendation": saved,
    }


def health_check():
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": "Reply with the single word OK."}],
        temperature=0,
        max_tokens=5,
    )
    return {
        "status": "ok",
        "model": OLLAMA_MODEL,
        "reply": (response.choices[0].message.content or "").strip(),
    }
