import os
import re
from pathlib import Path

import requests


REQUIRED_RAG_TOOLS = (
    "refresh_corpus",
    "retrieve_context",
    "answer_question",
)


def collect(
    app_dir,
    repo_root,
):
    app_dir = Path(app_dir)

    rag_dir = (
        app_dir.parent
        / "rag-server"
    )

    required_paths = [
        rag_dir / "rag_pipeline.py",
        rag_dir / "rag_server.py",
        rag_dir / "rag_http_server.py",
        rag_dir / "rag_eval.py",
        rag_dir / "requirements.txt",
        rag_dir / "retrieval-metrics.md",
    ]

    missing = [
        str(path)
        for path in required_paths
        if not path.is_file()
    ]

    if missing:
        return (
            False,
            "RAG evidence incomplete. Missing: "
            + ", ".join(missing),
        )

    pipeline_text = (
        rag_dir
        .joinpath("rag_pipeline.py")
        .read_text(
            encoding="utf-8"
        )
    )

    missing_tools = [
        tool
        for tool in REQUIRED_RAG_TOOLS
        if f"def {tool}" not in pipeline_text
    ]

    if missing_tools:
        return (
            False,
            "RAG pipeline missing required tools: "
            + ", ".join(missing_tools),
        )

    required_contract_terms = [
        "citations",
        "confidence_category",
        "Insufficient context.",
    ]

    missing_contract = [
        term
        for term in required_contract_terms
        if term not in pipeline_text
    ]

    if missing_contract:
        return (
            False,
            "RAG grounding contract incomplete: "
            + ", ".join(missing_contract),
        )

    metrics_text = (
        rag_dir
        .joinpath(
            "retrieval-metrics.md"
        )
        .read_text(
            encoding="utf-8"
        )
    )

    p_at_5 = re.findall(
        r"P@5:\s*([0-9.]+)",
        metrics_text,
    )

    r_at_5 = re.findall(
        r"R@5:\s*([0-9.]+)",
        metrics_text,
    )

    if not p_at_5 or not r_at_5:
        return (
            False,
            "RAG retrieval metrics are missing.",
        )

    rag_url = os.getenv(
        "RAG_SERVER_URL",
        "http://localhost:5200",
    ).rstrip("/")

    try:
        response = requests.get(
            f"{rag_url}/health",
            timeout=5,
        )

        response.raise_for_status()

        health = response.json()

    except requests.RequestException as exc:
        return (
            False,
            "RAG server is not reachable: "
            f"{exc}",
        )

    evidence = (
        "RAG VALIDATION EVIDENCE\n"
        f"- Live service: {rag_url}\n"
        f"- Health: {health}\n"
        "- Required tools present: "
        "refresh_corpus, retrieve_context, answer_question\n"
        "- Grounding contract present: citations, confidence category, "
        "insufficient-context handling\n"
        f"- Retrieval metrics recorded: {len(p_at_5)} P@5 values and "
        f"{len(r_at_5)} R@5 values\n"
        "- Required RAG implementation files are present."
    )

    try:
        answer_response = requests.post(
            f"{rag_url}/answer",
            json={
                "query":
                    "What expertise is required for "
                    "Advanced Software Development?",
                "k":
                    5,
                "caller":
                    "agentic-rag-validation",
            },
            timeout=120,
        )

        answer_response.raise_for_status()

        answer_result = (
            answer_response.json()
        )

    except requests.RequestException as exc:
        return (
            False,
            "Live RAG answer validation failed: "
            f"{exc}",
        )

    if (
        answer_result.get("status")
        != "success"
    ):
        return (
            False,
            "Live RAG answer returned "
            "a non-success result.",
        )

    citations = (
        answer_result.get(
            "citations",
            [],
        )
    )

    confidence = (
        answer_result.get(
            "confidence_category"
        )
    )

    answer = (
        answer_result.get(
            "answer",
            ""
        )
    )

    if not citations:
        return (
            False,
            "Live grounded answer returned "
            "without citations.",
        )

    if not confidence:
        return (
            False,
            "Live grounded answer returned "
            "without confidence.",
        )

    try:
        insufficient_response = requests.post(
            f"{rag_url}/answer",
            json={
                "query":
                    "What colour is the university "
                    "mascot's private helicopter?",
                "k":
                    5,
                "caller":
                    "agentic-rag-validation",
            },
            timeout=120,
        )

        insufficient_response.raise_for_status()

        insufficient_result = (
            insufficient_response.json()
        )

    except requests.RequestException as exc:
        return (
            False,
            "Insufficient-context validation failed: "
            f"{exc}",
        )

    insufficient_answer = (
        insufficient_result.get(
            "answer",
            ""
        )
    )

    if (
        insufficient_answer
        != "Insufficient context."
    ):
        return (
            False,
            "RAG failed insufficient-context test. "
            f"Returned: {insufficient_answer}"
        )

    evidence = (
        "RAG VALIDATION EVIDENCE\n"
        f"- Live service: {rag_url}\n"
        f"- Health: {health}\n"
        "- Required tools present: "
        "refresh_corpus, retrieve_context, answer_question\n"
        "- Grounding contract present: citations, confidence category, "
        "insufficient-context handling\n"
        f"- Retrieval metrics recorded: {len(p_at_5)} P@5 values and "
        f"{len(r_at_5)} R@5 values\n"
        f"- Live grounded answer: {answer}\n"
        f"- Live citations returned: {len(citations)}\n"
        f"- Live confidence category: {confidence}\n"
        "- Insufficient-context test: PASS\n"
        "- Required RAG implementation files are present."
    )

    return True, evidence