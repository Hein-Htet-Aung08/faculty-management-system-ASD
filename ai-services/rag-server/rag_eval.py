from pathlib import Path

from rag_pipeline import (
    retrieve_context,
)


METRICS_PATH = (
    Path(__file__)
    .resolve()
    .parent
    / "retrieval-metrics.md"
)


# ============================================================
# Student 1 - Staff Management Benchmarks
# ============================================================

STUDENT1_BENCHMARKS = [
    # Add Student 1 benchmark queries here.
    #
    # Example structure:
    #
    # {
    #     "query": "...",
    #     "relevant_keywords": [
    #         "...",
    #     ],
    #     "expected_relevant": 1,
    # },
]


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================

STUDENT2_BENCHMARKS = [
    # OWNER: Student 2 - Hein
    #
    # Add Student 2 RAG evaluation queries here after
    # Student 2 context loading is implemented.
]


# ============================================================
# Student 3 - Workload & Availability Management
# ============================================================

STUDENT3_BENCHMARKS = [
    # Add Student 3 benchmark queries here.
]


# ============================================================
# Student 4 - Research & Grant Management
# ============================================================

STUDENT4_BENCHMARKS = [
    # Add Student 4 benchmark queries here.
]


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================

STUDENT5_BENCHMARKS = [
    # Add Student 5 benchmark queries here.
]


# ============================================================
# Common Benchmark Collection
# ============================================================

BENCHMARKS = (
    STUDENT1_BENCHMARKS
    + STUDENT2_BENCHMARKS
    + STUDENT3_BENCHMARKS
    + STUDENT4_BENCHMARKS
    + STUDENT5_BENCHMARKS
)


def is_relevant(
    text,
    keywords,
):
    lowered = (
        text.lower()
    )

    return any(
        keyword.lower()
        in lowered
        for keyword
        in keywords
    )


def evaluate_query(
    benchmark,
):
    response = (
        retrieve_context(
            benchmark["query"],
            5,
        )
    )

    results = (
        response.get(
            "results",
            [],
        )[:5]
    )

    relevant = [
        result
        for result in results
        if is_relevant(
            result.get(
                "text",
                "",
            ),
            benchmark[
                "relevant_keywords"
            ],
        )
    ]

    precision_at_5 = (
        len(relevant)
        / 5
    )

    raw_recall_at_5 = (
        len(relevant)
        / max(
            benchmark[
                "expected_relevant"
            ],
            1,
        )
    )

    recall_at_5 = min(
        1.0,
        raw_recall_at_5,
    )

    return {
        "query":
            benchmark[
                "query"
            ],
        "retrieved_chunk_ids":
            [
                result.get(
                    "chunk_id"
                )
                for result
                in results
            ],
        "relevant_chunk_ids":
            [
                result.get(
                    "chunk_id"
                )
                for result
                in relevant
            ],
        "p_at_5":
            precision_at_5,
        "r_at_5":
            recall_at_5,
    }


def write_metrics_report(
    results,
):
    lines = [
        "# Retrieval Metrics",
        "",
    ]

    if not results:
        lines.extend(
            [
                (
                    "No benchmark queries "
                    "have been configured yet."
                ),
                "",
            ]
        )

    for result in results:
        lines.append(
            f"## {result['query']}"
        )

        lines.append(
            (
                "- Retrieved: "
                f"{result['retrieved_chunk_ids']}"
            )
        )

        lines.append(
            (
                "- Relevant: "
                f"{result['relevant_chunk_ids']}"
            )
        )

        lines.append(
            (
                "- P@5: "
                f"{result['p_at_5']}"
            )
        )

        lines.append(
            (
                "- R@5: "
                f"{result['r_at_5']}"
            )
        )

        lines.append(
            ""
        )

    METRICS_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    results = []

    for benchmark in BENCHMARKS:
        result = (
            evaluate_query(
                benchmark
            )
        )

        results.append(
            result
        )

        print(
            "Query:",
            result["query"],
        )

        print(
            "Retrieved:",
            result[
                "retrieved_chunk_ids"
            ],
        )

        print(
            "Relevant:",
            result[
                "relevant_chunk_ids"
            ],
        )

        print(
            "P@5:",
            result[
                "p_at_5"
            ],
        )

        print(
            "R@5:",
            result[
                "r_at_5"
            ],
        )

        print(
            "---"
        )

    if not BENCHMARKS:
        print(
            "No RAG benchmarks configured yet."
        )

    write_metrics_report(
        results
    )


if __name__ == "__main__":
    main()