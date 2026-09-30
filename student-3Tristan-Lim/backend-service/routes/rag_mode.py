import requests
from flask import Blueprint, jsonify, request

from services import rag_api

rag_bp = Blueprint("rag_mode", __name__, url_prefix="/rag")

AVAILABLE_TOOLS = ["refresh_corpus", "retrieve_context", "answer_question"]


def _mode_active():
    return rag_api.rag_enabled() and request.headers.get("X-RAG-Mode", "").strip().lower() == "on"


def _disabled_response():
    if not rag_api.rag_enabled():
        return jsonify({"error": "RAG is disabled on this server (RAG_ENABLED=false)."}), 503
    return jsonify({"error": "RAG Mode is off. Send 'X-RAG-Mode: on' to use these tools."}), 400


def _arg(name, default=""):
    if request.is_json:
        value = (request.get_json(silent=True) or {}).get(name)
        if value is not None:
            return str(value)
    return request.values.get(name, default)


@rag_bp.get("/health")
def health():
    status = {
        "rag_enabled": rag_api.rag_enabled(),
        "rag_mode_active": _mode_active(),
        "tools": AVAILABLE_TOOLS,
        "rag_service_url": rag_api.RAG_SERVICE_URL,
    }

    try:
        status["rag_service"] = rag_api.rag_service_health()
    except requests.RequestException as exc:
        status["rag_service_error"] = str(exc)
        return jsonify(status), 503

    return jsonify(status), 200


@rag_bp.post("/refresh")
def refresh():
    if not _mode_active():
        return _disabled_response()

    caller = _arg("caller", "student").strip() or "student"
    try:
        payload = rag_api.call_rag_service("/refresh", {"caller": caller})
        return jsonify(payload), 200
    except requests.RequestException as exc:
        return jsonify({"status": "error", "error": str(exc)}), 503


@rag_bp.post("/retrieve")
def retrieve():
    if not _mode_active():
        return _disabled_response()

    query = _arg("query").strip()
    if not query:
        return jsonify({"status": "error", "error": "query is required"}), 400

    k = int(_arg("k", "5") or 5)
    try:
        payload = rag_api.call_rag_service(
            "/retrieve", {"query": query, "k": k, "caller": "student"}
        )
        return jsonify(payload), 200
    except requests.RequestException as exc:
        return jsonify({"status": "error", "error": str(exc)}), 503


@rag_bp.post("/answer")
def answer():
    if not _mode_active():
        return _disabled_response()

    query = _arg("query").strip()
    if not query:
        return jsonify({"status": "error", "error": "query is required"}), 400

    k = int(_arg("k", "5") or 5)
    try:
        payload = rag_api.call_rag_service(
            "/answer", {"query": query, "k": k, "caller": "student"}
        )
        return jsonify(payload), 200
    except requests.RequestException as exc:
        return jsonify({"status": "error", "error": str(exc)}), 503
