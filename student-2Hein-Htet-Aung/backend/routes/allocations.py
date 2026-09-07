from flask import Blueprint, jsonify, request
import requests

from services.allocation_rules import validate_allocation
from services.database_api import (
    get_subject_offer_by_id_response,
    get_classroom_by_id_response,
    get_teaching_allocations,
    get_teaching_allocation_by_id_response,
    create_teaching_allocation_response,
    update_teaching_allocation_response,
    delete_teaching_allocation_response,
)
from services.staff_api import get_staff_by_id_response
from views.html_formatters import (
    format_teaching_allocation_html,
    format_teaching_allocations_html,
)
from services.workload_api import get_staff_availability_slots


allocations_bp = Blueprint("allocations", __name__)


def resolve_staff(allocation):
    staff_id = allocation["assigned_staff_member"]

    if staff_id is None:
        allocation["staff_name"] = None
        return allocation

    try:
        response = get_staff_by_id_response(staff_id)

        if response.status_code == 404:
            updated_allocation = allocation.copy()
            updated_allocation["assigned_staff_member"] = None
            updated_allocation["allocation_status"] = "NEEDS_ASSIGNMENT"

            update_response = update_teaching_allocation_response(
                allocation["allocation_id"],
                updated_allocation,
            )

            update_response.raise_for_status()

            updated_allocation["staff_name"] = None

            return updated_allocation

        response.raise_for_status()

        allocation["staff_name"] = response.json()["name"]

        return allocation

    except requests.RequestException:
        allocation["staff_name"] = "Unavailable"
        return allocation


def load_validation_context(data):
    offer_id = str(data.get("offer_id", "")).strip().upper()
    classroom_id = str(data.get("classroom_id", "")).strip().upper()
    staff_id = data.get("assigned_staff_member")

    subject_offer = None
    classroom = None
    staff = None
    staff_checked = False
    staff_availability = None

    if offer_id:
        response = get_subject_offer_by_id_response(offer_id)

        if response.status_code == 200:
            subject_offer = response.json()
        elif response.status_code != 404:
            response.raise_for_status()

    if classroom_id:
        response = get_classroom_by_id_response(classroom_id)

        if response.status_code == 200:
            classroom = response.json()
        elif response.status_code != 404:
            response.raise_for_status()

    if staff_id is not None:
        try:
            staff_id = int(staff_id)
        except (TypeError, ValueError):
            staff_id = None
        else:
            response = get_staff_by_id_response(staff_id)
            staff_checked = True

            if response.status_code == 200:
                staff = response.json()
                staff_availability = get_staff_availability_slots(staff_id)

            elif response.status_code != 404:
                response.raise_for_status()

    allocations = get_teaching_allocations()

    return (
        subject_offer,
        classroom,
        allocations,
        staff,
        staff_checked,
        staff_availability,
    )


@allocations_bp.get("/teaching-allocations")
def get_teaching_allocations_route():
    try:
        allocations = get_teaching_allocations()

        offer_id = request.args.get("offer_id", "").strip().upper()
        classroom_id = request.args.get("classroom_id", "").strip().upper()
        staff_id = request.args.get("staff_id", "").strip()
        day = request.args.get("day", "").strip().upper()
        status = request.args.get("status", "").strip().upper()

        if offer_id:
            allocations = [
                allocation
                for allocation in allocations
                if allocation["offer_id"] == offer_id
            ]

        if classroom_id:
            allocations = [
                allocation
                for allocation in allocations
                if allocation["classroom_id"] == classroom_id
            ]

        if staff_id:
            if not staff_id.isdigit():
                return "<p>Staff ID must be valid.</p>", 400

            allocations = [
                allocation
                for allocation in allocations
                if allocation["assigned_staff_member"] == int(staff_id)
            ]

        if day:
            allocations = [
                allocation
                for allocation in allocations
                if allocation["day"] == day
            ]

        if status:
            allocations = [
                allocation
                for allocation in allocations
                if allocation["allocation_status"] == status
            ]

        allocations = [
            resolve_staff(allocation)
            for allocation in allocations
        ]

        return format_teaching_allocations_html(allocations), 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve teaching allocations.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@allocations_bp.post("/teaching-allocations/validate")
def validate_teaching_allocation():
    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            {
                "valid": False,
                "errors": ["Teaching allocation data is required."],
            }
        ), 400

    try:
        (
            subject_offer,
            classroom,
            allocations,
            staff,
            staff_checked,
            staff_availability,
        ) = load_validation_context(data)

        result = validate_allocation(
            data,
            subject_offer,
            classroom,
            allocations,
            staff=staff,
            staff_checked=staff_checked,
            staff_availability=staff_availability,
        )

        return jsonify(result), 200

    except requests.RequestException as exc:
        return jsonify(
            {
                "valid": False,
                "errors": [
                    "Unable to complete allocation validation."
                ],
                "details": str(exc),
            }
        ), 503


@allocations_bp.get("/teaching-allocations/<int:allocation_id>")
def get_teaching_allocation_by_id(allocation_id):
    try:
        response = get_teaching_allocation_by_id_response(allocation_id)

        if response.status_code == 404:
            return "<p>Teaching allocation not found.</p>", 404

        response.raise_for_status()

        allocation = resolve_staff(response.json())

        return format_teaching_allocation_html(allocation), 200

    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve teaching allocation.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@allocations_bp.post("/teaching-allocations")
def create_teaching_allocation():
    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            {
                "error": "Teaching allocation data is required."
            }
        ), 400

    if data.get("assigned_staff_member") is None:
        data["allocation_status"] = "NEEDS_ASSIGNMENT"
    elif not data.get("allocation_status"):
        data["allocation_status"] = "PENDING"

    try:
        (
            subject_offer,
            classroom,
            allocations,
            staff,
            staff_checked,
            staff_availability,
        ) = load_validation_context(data)

        validation = validate_allocation(
            data,
            subject_offer,
            classroom,
            allocations,
            staff=staff,
            staff_checked=staff_checked,
            staff_availability=staff_availability,
        )

        if not validation["valid"]:
            return jsonify(validation), 400

        print("DATA SENT TO DATABASE:", data, flush=True)

        response = create_teaching_allocation_response(data)

        print("DATABASE RECEIVED:", repr(data), flush=True)
        print(
            "STAFF:",
            repr(data.get("assigned_staff_member")),
            "STATUS:",
            repr(data.get("allocation_status")),
            flush=True,
        )

        if response.status_code == 400:
            return jsonify(
                {
                    "error": response.json().get(
                        "error",
                        "Unable to create teaching allocation.",
                    )
                }
            ), 400

        response.raise_for_status()

        return jsonify(
            {
                "message": "Teaching allocation created."
            }
        ), 201

    except requests.RequestException as exc:
        return jsonify(
            {
                "error": "Failed to create teaching allocation.",
                "details": str(exc),
            }
        ), 503


@allocations_bp.put("/teaching-allocations/<int:allocation_id>")
def update_teaching_allocation(allocation_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify(
            {
                "error": "Teaching allocation data is required."
            }
        ), 400

    if data.get("assigned_staff_member") is None:
        data["allocation_status"] = "NEEDS_ASSIGNMENT"

    try:
        existing_response = get_teaching_allocation_by_id_response(
            allocation_id
        )

        if existing_response.status_code == 404:
            return jsonify(
                {
                    "error": "Teaching allocation not found."
                }
            ), 404

        existing_response.raise_for_status()

        (
            subject_offer,
            classroom,
            allocations,
            staff,
            staff_checked,
            staff_availability,
        ) = load_validation_context(data)

        validation = validate_allocation(
            data,
            subject_offer,
            classroom,
            allocations,
            staff=staff,
            staff_checked=staff_checked,
            staff_availability=staff_availability,
            exclude_allocation_id=allocation_id,
        )

        if not validation["valid"]:
            return jsonify(validation), 400

        response = update_teaching_allocation_response(
            allocation_id,
            data,
        )

        if response.status_code == 404:
            return jsonify(
                {
                    "error": "Teaching allocation not found."
                }
            ), 404

        if response.status_code == 400:
            return jsonify(
                {
                    "error": response.json().get(
                        "error",
                        "Unable to update teaching allocation.",
                    )
                }
            ), 400

        response.raise_for_status()

        return jsonify(
            {
                "message": "Teaching allocation updated."
            }
        ), 200

    except requests.RequestException as exc:
        return jsonify(
            {
                "error": "Failed to update teaching allocation.",
                "details": str(exc),
            }
        ), 503


@allocations_bp.delete("/teaching-allocations/<int:allocation_id>")
def delete_teaching_allocation(allocation_id):
    try:
        response = delete_teaching_allocation_response(allocation_id)

        if response.status_code == 404:
            return jsonify(
                {
                    "error": "Teaching allocation not found."
                }
            ), 404

        response.raise_for_status()

        return jsonify(
            {
                "message": "Teaching allocation deleted."
            }
        ), 200

    except requests.RequestException as exc:
        return jsonify(
            {
                "error": "Failed to delete teaching allocation.",
                "details": str(exc),
            }
        ), 503