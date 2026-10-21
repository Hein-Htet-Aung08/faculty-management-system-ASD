import os
import requests

RAG_SERVER_URL = os.environ.get("RAG_SERVER_URL", "http://host.docker.internal:5200")


def rag_ask(query: str, k: int = 5) -> dict:
    try:
        # llama3.1:8b generation on a CPU-only box can take well over two
        # minutes; the RAG server's own /answer call to Ollama already
        # allows 120s, so this needs more headroom than that or a slow
        # correct answer gets reported as "unavailable" before it lands.
        resp = requests.post(f"{RAG_SERVER_URL}/answer", json={"query": query, "k": k}, timeout=240)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"RAG server unavailable: {e}", "answer": None, "citations": [], "confidence_category": "unavailable"}


def rag_retrieve(query: str, k: int = 5) -> dict:
    try:
        resp = requests.post(f"{RAG_SERVER_URL}/retrieve", json={"query": query, "k": k}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"RAG server unavailable: {e}", "results": []}


def rag_refresh() -> dict:
    try:
        resp = requests.post(f"{RAG_SERVER_URL}/refresh", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        return {"error": f"RAG server unavailable: {e}"}
