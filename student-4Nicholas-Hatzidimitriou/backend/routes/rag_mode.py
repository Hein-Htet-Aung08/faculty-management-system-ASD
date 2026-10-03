import os
from functools import wraps

from flask import Blueprint, request, jsonify

from services.rag_api import rag_ask, rag_refresh

rag_bp = Blueprint("rag_mode", __name__)


def _rag_mode_active():
    return os.environ.get("RAG_ENABLED", "false").lower() == "true"


def require_rag_mode(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _rag_mode_active():
            return jsonify({"error": "RAG mode is off. The server needs RAG_ENABLED set."}), 403
        return fn(*args, **kwargs)

    return wrapper


@rag_bp.route("/api/rag/ask", methods=["POST"])
@require_rag_mode
def ask():
    body = request.get_json(force=True)
    query = body.get("query", "")
    if not query:
        return jsonify({"error": "query is required"}), 400
    return jsonify(rag_ask(query))


@rag_bp.route("/api/rag/refresh", methods=["POST"])
@require_rag_mode
def refresh():
    return jsonify(rag_refresh())
