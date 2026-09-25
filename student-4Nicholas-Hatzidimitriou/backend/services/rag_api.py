import os
import requests

RAG_SERVER_URL = os.environ.get("RAG_SERVER_URL", "http://host.docker.internal:5003")

def rag_ask(query: str) -> dict:
    try:
        resp = requests.post(f"{RAG_SERVER_URL}/answer", json={"query": query}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"RAG server unavailable: {e}", "answer": None, "citations": [], "confidence_category": "unavailable"}

def rag_refresh() -> dict:
    try:
        resp = requests.post(f"{RAG_SERVER_URL}/refresh", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"RAG server unavailable: {e}"}
