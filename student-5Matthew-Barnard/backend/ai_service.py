import json
import os
from datetime import date

from openai import OpenAI

import database_client
import staff_client
from prompt_loader import load_prompt
from requests import RequestException

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
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
    try:
        staff_details = staff_client.get_staff_context(staff_id)
    except (RequestException, ValueError):
        staff_details = None
    return {
        "staffID": staff_id,
        "staffDetails": staff_details,
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
    allowed_goal_ids = [goal["goalID"] for goal in context["developmentGoals"]]
    allowed_training_titles = [
        program["title"] for program in context["availableTrainingPrograms"]
    ]
    messages = [
        {"role": "system", "content": load_prompt("development_system_prompt.txt")},
        {
            "role": "user",
            "content": (
                load_prompt("development_task_prompt.txt")
                + "\n\nSUPPLIED RECORDS\n"
                + json.dumps(context, indent=2)
                + "\n\nALLOWED OUTPUT VALUES (copy exactly)\n"
                + f"goalID: {json.dumps(allowed_goal_ids)}\n"
                + f"Training titles: {json.dumps(allowed_training_titles)}"
            ),
        },
    ]

    # Small local models occasionally ignore a catalogue constraint. Give the
    # model one chance to correct its JSON, while validating both attempts with
    # the same application rules before anything is stored.
    validation_error = None
    for attempt in range(2):
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=350,
        )
        raw = response.choices[0].message.content or ""
        try:
            recommendation = _validate_recommendation(_extract_json(raw), context)
            break
        except ValueError as exc:
            validation_error = exc
            if attempt == 1:
                raise
            correction_context = {
                "staffID": context["staffID"],
                "staffDetails": context["staffDetails"],
                "performanceReviews": context["performanceReviews"],
                "developmentGoals": context["developmentGoals"],
            }
            # Use a short fresh correction prompt. This is more dependable for
            # the team's small local model than extending an already long chat.
            messages = [
                {
                    "role": "system",
                    "content": "Correct the rejected proposal. Output one JSON object only.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Rejected proposal: {raw}\nReason: {exc}. "
                        "Return keys goalID, recommendationType, recommendation, rationale. "
                        f"Allowed goal IDs are {json.dumps(allowed_goal_ids)}. If the type is "
                        "Training, the recommendation must include one title copied exactly "
                        f"from {json.dumps(allowed_training_titles)}. Otherwise change the type "
                        "to Goal, Mentoring, or Experience so it accurately describes the action. "
                        f"Evidence: {json.dumps(correction_context)}"
                    ),
                },
            ]
    else:
        raise validation_error

    saved_response = database_client.create_resource(
        "development-recommendations", recommendation
    )
    saved = database_client.read_json(saved_response)
    return {
        "mode": "validated-ai-recommendation",
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
