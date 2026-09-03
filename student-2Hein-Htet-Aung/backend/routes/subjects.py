from flask import Blueprint, request
import requests

from services.database_api import (
    get_subjects,
    get_subject_by_code_response,
    create_subject_response,
    update_subject_response,
    delete_subject_response,
    get_subject_offers,
    get_subject_offer_by_id_response,
    create_subject_offer_response,
    update_subject_offer_response,
    delete_subject_offer_response,
)
from views.html_formatters import (
    format_subject_html,
    format_subjects_html,
    format_subject_offer_html,
    format_subject_offers_html,
)


subjects_bp = Blueprint("subjects", __name__)


def validate_subject_data(data):
    errors = []

    subject_code = str(
        data.get("subject_code", "")
    ).strip()

    name = str(
        data.get("name", "")
    ).strip()

    required_expertise = str(
        data.get("required_expertise", "")
    ).strip()

    if not subject_code:
        errors.append(
            "Subject code is required."
        )
    elif (
        len(subject_code) != 5 or
        not subject_code.isdigit()
    ):
        errors.append(
            "Subject code must contain exactly 5 digits."
        )

    if not name:
        errors.append(
            "Subject name is required."
        )

    if not required_expertise:
        errors.append(
            "At least one required expertise is required."
        )
    else:
        expertise_items = (
            required_expertise.split(",")
        )

        if any(
            not item.strip()
            for item in expertise_items
        ):
            errors.append(
                "Required expertise contains an empty item."
            )

        if (
            ", " in required_expertise or
            " ," in required_expertise
        ):
            errors.append(
                "Required expertise must not contain spaces around commas."
            )

    if errors:
        return errors, None

    cleaned_data = {
        "subject_code": subject_code,
        "name": name,
        "required_expertise": ",".join(
            item.strip()
            for item in required_expertise.split(",")
        ),
    }

    return [], cleaned_data


@subjects_bp.get("/subjects")
def get_subjects_route():
    try:
        return (
            format_subjects_html(
                get_subjects()
            ),
            200,
        )
    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to retrieve subjects "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get(
    "/subjects/<string:subject_code>"
)
def get_subject_by_code(subject_code):
    subject_code = subject_code.strip()

    try:
        response = (
            get_subject_by_code_response(
                subject_code
            )
        )

        if response.status_code == 404:
            return (
                "<p>Subject not found.</p>",
                404,
            )

        response.raise_for_status()

        return (
            format_subject_html(
                response.json()
            ),
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to retrieve subject "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.post("/subjects")
def create_subject():
    data = request.get_json(
        silent=True
    )

    if not data:
        return (
            "<p>"
            "Subject data is required."
            "</p>",
            400,
        )

    errors, cleaned_data = (
        validate_subject_data(data)
    )

    if errors:
        return (
            "<p>"
            + " ".join(errors)
            + "</p>",
            400,
        )

    try:
        existing_response = (
            get_subject_by_code_response(
                cleaned_data[
                    "subject_code"
                ]
            )
        )

        if (
            existing_response.status_code
            == 200
        ):
            return (
                "<p>"
                "A subject with this "
                "subject code already exists."
                "</p>",
                400,
            )

        if (
            existing_response.status_code
            != 404
        ):
            existing_response.raise_for_status()

        response = create_subject_response(
            cleaned_data
        )

        if response.status_code == 400:
            error = response.json().get(
                "error",
                "Unable to create subject.",
            )

            return (
                f"<p>{error}</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>Subject created.</p>",
            201,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to create subject "
            "in database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.put(
    "/subjects/<string:subject_code>"
)
def update_subject(subject_code):
    data = request.get_json(
        silent=True
    )

    original_subject_code = (
        subject_code.strip()
    )

    if not data:
        return (
            "<p>"
            "Subject data is required."
            "</p>",
            400,
        )

    errors, cleaned_data = (
        validate_subject_data(data)
    )

    if errors:
        return (
            "<p>"
            + " ".join(errors)
            + "</p>",
            400,
        )

    try:
        existing_response = (
            get_subject_by_code_response(
                original_subject_code
            )
        )

        if (
            existing_response.status_code
            == 404
        ):
            return (
                "<p>Subject not found.</p>",
                404,
            )

        existing_response.raise_for_status()

        new_subject_code = (
            cleaned_data["subject_code"]
        )

        if (
            new_subject_code
            != original_subject_code
        ):
            duplicate_response = (
                get_subject_by_code_response(
                    new_subject_code
                )
            )

            if (
                duplicate_response.status_code
                == 200
            ):
                return (
                    "<p>"
                    "A subject with the new "
                    "subject code already exists."
                    "</p>",
                    400,
                )

            if (
                duplicate_response.status_code
                != 404
            ):
                duplicate_response.raise_for_status()

        response = update_subject_response(
            original_subject_code,
            cleaned_data,
        )

        if response.status_code == 404:
            return (
                "<p>Subject not found.</p>",
                404,
            )

        if response.status_code == 400:
            error = response.json().get(
                "error",
                "Unable to update subject.",
            )

            if (
                "FOREIGN KEY"
                in error.upper()
            ):
                return (
                    "<p>"
                    "Subject code cannot be "
                    "changed while subject offers "
                    "reference this subject."
                    "</p>",
                    400,
                )

            return (
                f"<p>{error}</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>Subject updated.</p>",
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to update subject "
            "in database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.delete(
    "/subjects/<string:subject_code>"
)
def delete_subject(subject_code):
    subject_code = subject_code.strip()

    if (
        len(subject_code) != 5 or
        not subject_code.isdigit()
    ):
        return (
            "<p>"
            "Subject code must contain "
            "exactly 5 digits."
            "</p>",
            400,
        )

    try:
        existing_response = (
            get_subject_by_code_response(
                subject_code
            )
        )

        if (
            existing_response.status_code
            == 404
        ):
            return (
                "<p>Subject not found.</p>",
                404,
            )

        existing_response.raise_for_status()

        response = delete_subject_response(
            subject_code
        )

        if response.status_code == 404:
            return (
                "<p>Subject not found.</p>",
                404,
            )

        if response.status_code == 400:
            error = response.json().get(
                "error",
                "Unable to delete subject.",
            )

            if (
                "FOREIGN KEY"
                in error.upper()
            ):
                return (
                    "<p>"
                    "Subject cannot be deleted "
                    "because one or more subject "
                    "offers reference it. Delete "
                    "those subject offers first."
                    "</p>",
                    409,
                )

            return (
                f"<p>{error}</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>Subject deleted.</p>",
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to delete subject "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get("/subject-offers")
def get_subject_offers_route():
    try:
        return (
            format_subject_offers_html(
                get_subject_offers()
            ),
            200,
        )
    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to retrieve subject offers "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get(
    "/subject-offers/<string:offer_id>"
)
def get_subject_offer_by_id(offer_id):
    offer_id = (
        offer_id.strip().upper()
    )

    try:
        response = (
            get_subject_offer_by_id_response(
                offer_id
            )
        )

        if response.status_code == 404:
            return (
                "<p>"
                "Subject offer not found."
                "</p>",
                404,
            )

        response.raise_for_status()

        return (
            format_subject_offer_html(
                response.json()
            ),
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to retrieve subject offer "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.post("/subject-offers")
def create_subject_offer():
    data = request.get_json(
        silent=True
    )

    if not data:
        return (
            "<p>"
            "Subject offer data is required."
            "</p>",
            400,
        )

    try:
        response = (
            create_subject_offer_response(
                data
            )
        )

        if response.status_code == 400:
            return (
                "<p>"
                + response.json().get(
                    "error",
                    "Unable to create "
                    "subject offer.",
                )
                + "</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>"
            "Subject offer created."
            "</p>",
            201,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to create subject offer "
            "in database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.put(
    "/subject-offers/<string:offer_id>"
)
def update_subject_offer(offer_id):
    data = request.get_json(
        silent=True
    )

    offer_id = (
        offer_id.strip().upper()
    )

    if not data:
        return (
            "<p>"
            "Subject offer data is required."
            "</p>",
            400,
        )

    try:
        response = (
            update_subject_offer_response(
                offer_id,
                data,
            )
        )

        if response.status_code == 404:
            return (
                "<p>"
                "Subject offer not found."
                "</p>",
                404,
            )

        if response.status_code == 400:
            return (
                "<p>"
                + response.json().get(
                    "error",
                    "Unable to update "
                    "subject offer.",
                )
                + "</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>"
            "Subject offer updated."
            "</p>",
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to update subject offer "
            "in database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.delete(
    "/subject-offers/<string:offer_id>"
)
def delete_subject_offer(offer_id):
    offer_id = (
        offer_id.strip().upper()
    )

    try:
        response = (
            delete_subject_offer_response(
                offer_id
            )
        )

        if response.status_code == 404:
            return (
                "<p>"
                "Subject offer not found."
                "</p>",
                404,
            )

        if response.status_code == 400:
            return (
                "<p>"
                + response.json().get(
                    "error",
                    "Unable to delete "
                    "subject offer.",
                )
                + "</p>",
                400,
            )

        response.raise_for_status()

        return (
            "<p>"
            "Subject offer deleted."
            "</p>",
            200,
        )

    except requests.RequestException as exc:
        return (
            "<p>"
            "Failed to delete subject offer "
            "from database-service."
            "</p>"
            f"<pre>{exc}</pre>",
            503,
        )