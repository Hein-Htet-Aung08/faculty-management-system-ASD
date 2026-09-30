from flask import Blueprint, request, jsonify
from services.rag_api import rag_ask, rag_refresh, rag_retrieve

rag_bp = Blueprint("rag_mode", __name__)


@rag_bp.route("/rag/ask", methods=["POST"])
def ask():
    body = request.get_json(force=True)
    query = body.get("query", "")
    if not query:
        return jsonify({"error": "query is required"}), 400
    return jsonify(rag_ask(query, body.get("k", 5)))


@rag_bp.route("/rag/retrieve", methods=["POST"])
def retrieve():
    body = request.get_json(force=True)
    query = body.get("query", "")
    if not query:
        return jsonify({"error": "query is required"}), 400
    return jsonify(rag_retrieve(query, body.get("k", 5)))


@rag_bp.route("/rag/refresh", methods=["POST"])
def refresh():
    return jsonify(rag_refresh())
