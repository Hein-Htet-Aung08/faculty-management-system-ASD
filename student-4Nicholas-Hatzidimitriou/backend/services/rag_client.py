import os

import requests

RAG_SERVICE_URL = os.environ.get("RAG_SERVICE_URL", "http://localhost:5204")


def get_retrieved_context(project_id):
    try:
        response = requests.get(
            f"{RAG_SERVICE_URL}/retrieve", params={"project_id": project_id}, timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return data.get("context", [])
    except requests.exceptions.RequestException:
        return []
