import os
import re
from pathlib import Path

import requests


REQUIRED_RAG_TOOLS = (
    "refresh_corpus",
    "retrieve_context",
    "answer_question",
)

VALID_CONFIDENCE = {
    "Low",
    "Medium",
    "High",
}


def _post_json(
    base_url,
    path,
    payload,
    timeout,
):
    response = requests.post(
        f"{base_url}{path}",
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


def _line_count(
    path,
):
    if not path.is_file():
        return 0

    return len(
        path.read_text(
            encoding="utf-8",
        ).splitlines()
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

    benchmark_queries = re.findall(
        r"^## (.+)$",
        metrics_text,
        flags=re.MULTILINE,
    )

    p_at_5 = [
        float(value)
        for value in re.findall(
            r"P@5:\s*([0-9.]+)",
            metrics_text,
        )
    ]

    r_at_5 = [
        float(value)
        for value in re.findall(
            r"R@5:\s*([0-9.]+)",
            metrics_text,
        )
    ]

    if (
        not benchmark_queries
        or not p_at_5
        or not r_at_5
    ):
        return (
            False,
            "RAG retrieval metrics are missing.",
        )

    rag_url = os.getenv(
        "RAG_SERVER_URL",
        "http://localhost:5200",
    ).rstrip("/")

    audit_path = (
        rag_dir
        / "rag-audit.jsonl"
    )

    audit_before = (
        _line_count(
            audit_path
        )
    )

    try:
        response = requests.get(
            f"{rag_url}/health",
            timeout=5,
        )

        response.raise_for_status()

        health = response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return (
            False,
            "RAG health validation failed: "
            f"{exc}",
        )

    if (
        health.get("status")
        != "ok"
    ):
        return (
            False,
            "RAG health endpoint did not "
            "report status=ok.",
        )

    try:
        refresh_result = _post_json(
            rag_url,
            "/refresh",
            {
                "caller":
                    "agentic-rag-validation",
            },
            30,
        )

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return (
            False,
            "RAG corpus refresh validation failed: "
            f"{exc}",
        )

    if (
        refresh_result.get("status")
        != "success"
    ):
        return (
            False,
            "RAG corpus refresh returned "
            "a non-success result.",
        )

    if (
        refresh_result.get(
            "chunk_count",
            0,
        )
        <= 0
    ):
        return (
            False,
            "RAG corpus refresh produced "
            "zero chunks.",
        )

    if (
        refresh_result.get(
            "vector_store_status"
        )
        != "ready"
    ):
        return (
            False,
            "RAG vector store did not "
            "report ready status.",
        )

    validation_query = (
        benchmark_queries[0]
    )

    try:
        retrieve_result = _post_json(
            rag_url,
            "/retrieve",
            {
                "query":
                    validation_query,
                "k":
                    5,
                "caller":
                    "agentic-rag-validation",
            },
            15,
        )

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return (
            False,
            "RAG retrieval validation failed: "
            f"{exc}",
        )

    retrieved = (
        retrieve_result.get(
            "results",
            [],
        )
    )

    if (
        retrieve_result.get("status")
        != "success"
        or not retrieved
    ):
        return (
            False,
            "RAG retrieval returned "
            "no validation evidence.",
        )

    try:
        answer_result = _post_json(
            rag_url,
            "/answer",
            {
                "query":
                    validation_query,
                "k":
                    5,
                "caller":
                    "agentic-rag-validation",
            },
            120,
        )

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
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

    answer = (
        answer_result.get(
            "answer",
            "",
        )
        .strip()
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

    if (
        not answer
        or answer
        == "Insufficient context."
    ):
        return (
            False,
            "Positive grounded-answer test "
            "did not produce an answer.",
        )

    if not citations:
        return (
            False,
            "Live grounded answer returned "
            "without citations.",
        )

    for citation in citations:
        if (
            not citation.get(
                "chunk_id"
            )
            or not citation.get(
                "source_id"
            )
        ):
            return (
                False,
                "A RAG citation is missing "
                "chunk or source identity.",
            )

    if (
        confidence
        not in VALID_CONFIDENCE
    ):
        return (
            False,
            "Live grounded answer returned "
            "an invalid confidence category.",
        )

    negative_query = (
        "zzzz_agentic_validation_"
        "no_matching_context_987654321"
    )

    try:
        insufficient_result = _post_json(
            rag_url,
            "/answer",
            {
                "query":
                    negative_query,
                "k":
                    5,
                "caller":
                    "agentic-rag-validation",
            },
            120,
        )

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return (
            False,
            "Insufficient-context validation failed: "
            f"{exc}",
        )

    if (
        insufficient_result.get(
            "answer"
        )
        != "Insufficient context."
    ):
        return (
            False,
            "RAG failed insufficient-context test. "
            f"Returned: "
            f"{insufficient_result.get('answer')}"
        )

    audit_after = (
        _line_count(
            audit_path
        )
    )

    if (
        audit_after
        <= audit_before
    ):
        return (
            False,
            "RAG validation completed but "
            "no new audit records were written.",
        )

    mean_p = (
        sum(p_at_5)
        / len(p_at_5)
    )

    mean_r = (
        sum(r_at_5)
        / len(r_at_5)
    )

    evidence = (
        "RAG VALIDATION EVIDENCE\n"
        "- Structural files: PASS\n"
        "- Required tools: PASS "
        "(refresh_corpus, retrieve_context, answer_question)\n"
        f"- Live health: PASS ({health})\n"
        "- Corpus refresh: PASS "
        f"({refresh_result.get('chunk_count')} chunks, "
        "vector store ready)\n"
        "- Retrieval: PASS "
        f"({len(retrieved)} chunk(s), "
        f"mode={retrieve_result.get('retrieval_mode')})\n"
        f"- Validation query: {validation_query}\n"
        f"- Grounded answer: {answer}\n"
        f"- Citations: PASS ({len(citations)} returned)\n"
        f"- Confidence: PASS ({confidence})\n"
        "- Insufficient-context behaviour: PASS\n"
        "- Audit logging: PASS "
        f"({audit_after - audit_before} new record(s))\n"
        "- Retrieval metrics: "
        f"{len(p_at_5)} benchmark(s), "
        f"mean P@5={mean_p:.3f}, "
        f"mean R@5={mean_r:.3f}, "
        f"minimum R@5={min(r_at_5):.3f}"
    )

    return True, evidence