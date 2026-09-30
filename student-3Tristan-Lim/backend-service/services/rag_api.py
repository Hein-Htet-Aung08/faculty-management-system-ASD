import os

import requests

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:5303")
RAG_TIMEOUT = float(os.getenv("RAG_SERVICE_TIMEOUT", "180"))


def rag_enabled():
    return os.getenv("RAG_ENABLED", "true").strip().lower() in ("1", "true", "on", "yes")


def call_rag_service(path, payload):
    response = requests.post(f"{RAG_SERVICE_URL}{path}", json=payload, timeout=RAG_TIMEOUT)

    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()
        return {}

    if response.status_code >= 400:
        raise requests.HTTPError(
            f"rag-server {path} failed with status {response.status_code}: {data}",
            response=response,
        )

    return data


def rag_service_health():
    response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
    response.raise_for_status()
    return response.json()
