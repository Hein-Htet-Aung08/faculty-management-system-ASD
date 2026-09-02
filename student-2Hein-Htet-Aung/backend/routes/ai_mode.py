from flask import Blueprint, jsonify, request
import requests

from services.allocation_rules import is_staff_available
from services.database_api import (
    get_subject_by_code_response,
    get_subject_offer_by_id_response,
)
from services.llm_client import recommend_teaching_staff
from services.staff_api import (
    get_staff,
    get_staff_by_id_response,
    get_staff_expertise_response,
)
from services.workload_api import get_staff_workload_context


ai_mode_bp = Blueprint("ai_mode", __name__)


def get_staff_id(staff):
    return (
        staff.get("staffID")
        or staff.get("staff_id")
        or staff.get("id")
    )


def get_staff_name(staff):
    return (
        staff.get("name")
        or staff.get("staff_name")
        or f"Staff {get_staff_id(staff)}"
    )


def load_staff_expertise(staff_id):
    response = get_staff_expertise_response(staff_id)

    if response.status_code == 404:
        return []

    response.raise_for_status()

    data = response.json()

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "expertise" in data:
            return data["expertise"]

        if "results" in data:
            return data["results"]

    return data


def build_staff_candidate(staff, allocation):
    staff_id = get_staff_id(staff)

    expertise = load_staff_expertise(staff_id)

    workload = get_staff_workload_context(staff_id)

    availability_slots = workload["availability"]

    available = is_staff_available(
        availability_slots,
        allocation["day"],
        allocation["start_time"],
        allocation["end_time"],
    )

    return {
        "staff_id": staff_id,
        "staff_name": get_staff_name(staff),
        "department": staff.get("department"),
        "position": staff.get("position"),
        "expertise": expertise,
        "available": available,
        "availability": availability_slots,
        "workload_summary": workload["analysis"],
    }


def build_recommendation_context(data):
    offer_id = str(data.get("offer_id", "")).strip().upper()

    if not offer_id:
        return None, "offer_id is required.", 400

    offer_response = get_subject_offer_by_id_response(offer_id)

    if offer_response.status_code == 404:
        return None, "Subject offer not found.", 404

    offer_response.raise_for_status()

    offer = offer_response.json()

    subject_response = get_subject_by_code_response(
        offer["subject_code"]
    )

    if subject_response.status_code == 404:
        return None, "Subject not found.", 404

    subject_response.raise_for_status()

    subject = subject_response.json()

    staff_members = get_staff()

    candidates = []

    for staff in staff_members:
        staff_id = get_staff_id(staff)

        if staff_id is None:
            continue

        try:
            candidate = build_staff_candidate(
                staff,
                data,
            )
            candidates.append(candidate)

        except requests.RequestException:
            continue

    context = {
        "allocation": {
            "offer_id": offer_id,
            "subject_code": offer["subject_code"],
            "subject_name": subject["name"],
            "required_expertise": subject["required_expertise"],
            "day": data.get("day"),
            "date_range": data.get("date_range"),
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "class_type": data.get("class_type"),
            "expected_class_size": data.get(
                "expected_class_size"
            ),
        },
        "staff_candidates": candidates,
        "previous_recommendation_ids": data.get(
            "previous_recommendation_ids",
            [],
        ),
        "previous_failure_reasons": data.get(
            "previous_failure_reasons",
            [],
        ),
    }

    return context, None, 200


def review_recommendations(
    recommendations,
    context,
):
    candidates = {
        candidate["staff_id"]: candidate
        for candidate in context["staff_candidates"]
    }

    accepted = []
    rejected = []

    seen = set()

    for recommendation in recommendations[:3]:
        staff_id = recommendation.get("staff_id")

        try:
            staff_id = int(staff_id)
        except (TypeError, ValueError):
            rejected.append(
                {
                    "staff_id": staff_id,
                    "reason": "AI returned an invalid staff ID.",
                }
            )
            continue

        if staff_id in seen:
            rejected.append(
                {
                    "staff_id": staff_id,
                    "reason": "Duplicate recommendation.",
                }
            )
            continue

        seen.add(staff_id)

        candidate = candidates.get(staff_id)

        if candidate is None:
            rejected.append(
                {
                    "staff_id": staff_id,
                    "reason": "Staff member was not supplied to the AI.",
                }
            )
            continue

        try:
            response = get_staff_by_id_response(staff_id)

            if response.status_code == 404:
                rejected.append(
                    {
                        "staff_id": staff_id,
                        "reason": "Staff member no longer exists.",
                    }
                )
                continue

            response.raise_for_status()

        except requests.RequestException:
            rejected.append(
                {
                    "staff_id": staff_id,
                    "reason": "Staff member could not be verified.",
                }
            )
            continue

        if not candidate["available"]:
            rejected.append(
                {
                    "staff_id": staff_id,
                    "reason": "Staff member is unavailable during the requested time.",
                }
            )
            continue

        accepted.append(
            {
                "staff_id": staff_id,
                "staff_name": candidate["staff_name"],
                "rank": len(accepted) + 1,
                "reason": recommendation.get(
                    "reason",
                    "",
                ),
                "expertise": candidate["expertise"],
                "workload_summary": candidate[
                    "workload_summary"
                ],
            }
        )

    return accepted, rejected


@ai_mode_bp.post("/teaching-allocations/recommend")
def recommend_allocation_staff():
    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            {
                "error": "Teaching allocation data is required."
            }
        ), 400

    required_fields = [
        "offer_id",
        "day",
        "date_range",
        "start_time",
        "end_time",
        "class_type",
        "expected_class_size",
    ]

    missing = [
        field
        for field in required_fields
        if data.get(field) in (None, "")
    ]

    if missing:
        return jsonify(
            {
                "error": "Missing required fields.",
                "fields": missing,
            }
        ), 400

    try:
        context, error, status = build_recommendation_context(
            data
        )

        if error:
            return jsonify(
                {
                    "error": error
                }
            ), status

        ai_result = recommend_teaching_staff(context)

        recommendations = ai_result.get(
            "recommendations",
            [],
        )

        accepted, rejected = review_recommendations(
            recommendations,
            context,
        )

        return jsonify(
            {
                "recommendations": accepted,
                "rejected_recommendations": rejected,
                "can_generate_again": True,
            }
        ), 200

    except ValueError:
        return jsonify(
            {
                "error": "The AI returned an invalid response."
            }
        ), 502

    except requests.RequestException as exc:
        return jsonify(
            {
                "error": "A required service could not be reached.",
                "details": str(exc),
            }
        ), 503

    except Exception as exc:
        return jsonify(
            {
                "error": "Staff recommendation failed.",
                "details": str(exc),
            }
        ), 500