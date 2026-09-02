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


@subjects_bp.get("/subjects")
def get_subjects_route():
    try:
        return format_subjects_html(get_subjects()), 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve subjects from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get("/subjects/<string:subject_code>")
def get_subject_by_code(subject_code):
    subject_code = subject_code.strip()

    try:
        response = get_subject_by_code_response(subject_code)

        if response.status_code == 404:
            return "<p>Subject not found.</p>", 404

        response.raise_for_status()
        return format_subject_html(response.json()), 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve subject from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.post("/subjects")
def create_subject():
    data = request.get_json(silent=True)

    if not data:
        return "<p>Subject data is required.</p>", 400

    try:
        response = create_subject_response(data)

        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to create subject.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject created.</p>", 201
    except requests.RequestException as exc:
        return (
            "<p>Failed to create subject in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.put("/subjects/<string:subject_code>")
def update_subject(subject_code):
    data = request.get_json(silent=True)
    subject_code = subject_code.strip()

    if not data:
        return "<p>Subject data is required.</p>", 400

    try:
        response = update_subject_response(subject_code, data)

        if response.status_code == 404:
            return "<p>Subject not found.</p>", 404
        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to update subject.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject updated.</p>", 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to update subject in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.delete("/subjects/<string:subject_code>")
def delete_subject(subject_code):
    subject_code = subject_code.strip()

    try:
        response = delete_subject_response(subject_code)

        if response.status_code == 404:
            return "<p>Subject not found.</p>", 404
        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to delete subject.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject deleted.</p>", 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to delete subject from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get("/subject-offers")
def get_subject_offers_route():
    try:
        return format_subject_offers_html(get_subject_offers()), 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve subject offers from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.get("/subject-offers/<string:offer_id>")
def get_subject_offer_by_id(offer_id):
    offer_id = offer_id.strip().upper()

    try:
        response = get_subject_offer_by_id_response(offer_id)

        if response.status_code == 404:
            return "<p>Subject offer not found.</p>", 404

        response.raise_for_status()
        return format_subject_offer_html(response.json()), 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to retrieve subject offer from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.post("/subject-offers")
def create_subject_offer():
    data = request.get_json(silent=True)

    if not data:
        return "<p>Subject offer data is required.</p>", 400

    try:
        response = create_subject_offer_response(data)

        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to create subject offer.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject offer created.</p>", 201
    except requests.RequestException as exc:
        return (
            "<p>Failed to create subject offer in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.put("/subject-offers/<string:offer_id>")
def update_subject_offer(offer_id):
    data = request.get_json(silent=True)
    offer_id = offer_id.strip().upper()

    if not data:
        return "<p>Subject offer data is required.</p>", 400

    try:
        response = update_subject_offer_response(offer_id, data)

        if response.status_code == 404:
            return "<p>Subject offer not found.</p>", 404
        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to update subject offer.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject offer updated.</p>", 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to update subject offer in database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )


@subjects_bp.delete("/subject-offers/<string:offer_id>")
def delete_subject_offer(offer_id):
    offer_id = offer_id.strip().upper()

    try:
        response = delete_subject_offer_response(offer_id)

        if response.status_code == 404:
            return "<p>Subject offer not found.</p>", 404
        if response.status_code == 400:
            return f"<p>{response.json().get('error', 'Unable to delete subject offer.')}</p>", 400

        response.raise_for_status()
        return "<p>Subject offer deleted.</p>", 200
    except requests.RequestException as exc:
        return (
            "<p>Failed to delete subject offer from database-service.</p>"
            f"<pre>{exc}</pre>",
            503,
        )