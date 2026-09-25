import os
import re

import requests

DATABASE_SERVICE_URL = os.environ.get("DATABASE_SERVICE_URL", "http://localhost:5104")

MAX_RESULTS = 3

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "with",
    "is", "are", "this", "that", "into", "using", "based", "via", "from",
}

_WORD_RE = re.compile(r"[a-z0-9]+")


def _get(path, params=None):
    try:
        response = requests.get(f"{DATABASE_SERVICE_URL}{path}", params=params, timeout=10)
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(f"database-service unreachable at {DATABASE_SERVICE_URL}") from exc
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _words(*texts):
    combined = " ".join(t for t in texts if t).lower()
    return {w for w in _WORD_RE.findall(combined) if w not in _STOPWORDS}


def _overlap_score(target_words, candidate_words):
    if not target_words or not candidate_words:
        return 0
    return len(target_words & candidate_words)


def retrieve_context(project_id):
    target = _get(f"/projects/{project_id}")
    if target is None:
        raise ValueError(f"Project {project_id} does not exist.")

    department = target.get("department")
    target_words = _words(target.get("title"), target.get("description"))

    candidates = _get("/projects", {"department": department}) or []
    candidates = [c for c in candidates if c["projectID"] != target["projectID"]]

    scored = []
    for candidate in candidates:
        candidate_words = _words(candidate.get("title"), candidate.get("description"))
        score = _overlap_score(target_words, candidate_words)
        scored.append((score, candidate))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["projectID"]))
    top = scored[:MAX_RESULTS]

    snippets = []
    for _score, candidate in top:
        publications = _get("/publications", {"projectID": candidate["projectID"]}) or []
        pub_titles = [p["title"] for p in publications]

        snippet = (
            f'Past project in {candidate.get("department")}: "{candidate.get("title")}" '
            f'({candidate.get("status")}) - {candidate.get("description")}'
        )
        if pub_titles:
            snippet += f" Related publications: {', '.join(pub_titles)}."
        snippets.append(snippet)

    return snippets


if __name__ == "__main__":
    print("retrieve_context(1) - Computer Science, has a same-department sibling (project 4):")
    for snippet in retrieve_context(1):
        print(" -", snippet)

    print()
    print("retrieve_context(3) - Psychology, no same-department sibling (expect empty list):")
    print(" ", retrieve_context(3))
