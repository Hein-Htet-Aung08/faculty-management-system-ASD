from flask import Blueprint, request, jsonify
from services.rag_api import rag_ask, rag_refresh

rag_bp = Blueprint("rag_mode", __name__)

@rag_bp.route("/api/rag/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True)
    query = body.get("query", "")
    if not query:
        return jsonify({"error": "query is required"}), 400
    return jsonify(rag_ask(query))

@rag_bp.route("/api/rag/refresh", methods=["POST"])
def refresh():
    return jsonify(rag_refresh())
