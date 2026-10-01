import os

import requests


RAG_SERVER_URL = os.environ.get(
    "RAG_SERVER_URL",
    "http://host.docker.internal:5200",
)


def rag_ask(
    query: str,
    k: int = 5,
) -> dict:
    """
    Ask the shared local RAG server for a grounded answer.
    """

    try:
        response = requests.post(
            f"{RAG_SERVER_URL}/answer",
            json={
                "query": query,
                "k": k,
                "caller": "student2-backend",
            },
            timeout=120,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        return {
            "status": "error",
            "error": (
                "RAG server unavailable: "
                f"{exc}"
            ),
            "answer": None,
            "citations": [],
            "confidence_category":
                "unavailable",
        }


def rag_retrieve(
    query: str,
    k: int = 5,
) -> dict:
    """
    Retrieve context from the shared RAG server without
    invoking the language model.
    """

    try:
        response = requests.post(
            f"{RAG_SERVER_URL}/retrieve",
            json={
                "query": query,
                "k": k,
                "caller": "student2-backend",
            },
            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        return {
            "status": "error",
            "error": (
                "RAG server unavailable: "
                f"{exc}"
            ),
            "results": [],
        }


def rag_refresh() -> dict:
    """
    Ask the shared RAG service to rebuild its corpus.
    """

    try:
        response = requests.post(
            f"{RAG_SERVER_URL}/refresh",
            json={
                "caller":
                    "student2-backend",
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:
        return {
            "status": "error",
            "error": (
                "RAG server unavailable: "
                f"{exc}"
            ),
        }