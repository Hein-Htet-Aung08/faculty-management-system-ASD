import os

import requests


class RAGServiceError(Exception):
    pass


def enabled():
    return os.getenv("RAG_ENABLED", "false").lower() == "true"


def request_rag(path, payload, timeout):
    base_url = os.getenv("RAG_SERVER_URL", "http://localhost:5200").rstrip("/")
    try:
        response = requests.post(f"{base_url}/{path}", json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise RAGServiceError(f"RAG server is unavailable: {exc}") from exc
    try:
        result = response.json()
    except ValueError as exc:
        raise RAGServiceError("RAG server returned an invalid response") from exc
    if not isinstance(result, dict):
        raise RAGServiceError("RAG server returned an invalid response")
    if not response.ok or result.get("status") != "success":
        raise RAGServiceError(result.get("details") or result.get("error") or "RAG request failed")
    return result


def answer_question(query):
    result = request_rag(
        "answer", {"query": query, "k": 5, "caller": "student5-performance-development"}, 120
    )
    answer = str(result.get("answer") or "").strip()
    citations = result.get("citations")
    if not answer or answer.lower().startswith("insufficient context") or not isinstance(citations, list) or not citations:
        result["answer"] = "Insufficient context."
        result["citations"] = []
        result["confidence_category"] = "Insufficient"
    else:
        result["confidence_category"] = result.get("confidence_category") or "Unknown"
    return result


def refresh_corpus():
    return request_rag("refresh", {"caller": "student5-performance-development"}, 60)
