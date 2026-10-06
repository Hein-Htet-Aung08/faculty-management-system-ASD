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
    # Keywords match the seeded Staff Management data
    # (student-1-Andy-Lam/database/seed.py).
    {
        "query": "Which staff member has expertise in machine learning?",
        "relevant_keywords": [
            "Machine Learning",
        ],
        "expected_relevant": 1,
    },
    {
        "query": "What qualifications does Marcus Chen hold?",
        "relevant_keywords": [
            "PhD in Software Engineering",
        ],
        "expected_relevant": 1,
    },
    {
        "query": "Who works in the Computer Science department?",
        "relevant_keywords": [
            "Computer Science",
        ],
        "expected_relevant": 3,
    },
    {
        "query": "Which staff member is currently on leave?",
        "relevant_keywords": [
            "On Leave",
        ],
        "expected_relevant": 2,
    },
    {
        "query": "When is Fatima Ali available to teach?",
        "relevant_keywords": [
            "Staff availability for Fatima Ali",
        ],
        "expected_relevant": 1,
    },
]


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation
# ============================================================

STUDENT2_BENCHMARKS = [
    # OWNER: Student 2 - Hein
    #
    # Student 2 uses explicit gold chunk IDs because the corpus
    # contains several joined representations of the same data.
    # The gold chunks below represent the most appropriate evidence
    # for each information need.

    {
        "query":
            "What expertise is required for "
            "Advanced Software Development?",

        "relevant_chunk_ids": [
            "student2_subject_41114",
        ],
    },

    {
        "query":
            "What classroom is Advanced Software Development "
            "taught in?",

        "relevant_chunk_ids": [
            "student2_allocation_4",
            "student2_subject_allocation_summary_41114",
        ],
    },

    {
        "query":
            "What expertise is required for the subject "
            "allocated to classroom CB11.04.406?",

        "relevant_chunk_ids": [
            "student2_subject_allocation_summary_41114",
            "student2_allocation_4",
        ],
    },

    {
        "query":
            "When is Advanced Software Development taught, "
            "which classroom is it in, and what facilities "
            "does that room have?",

        "relevant_chunk_ids": [
            "student2_allocation_4",
            "student2_subject_allocation_summary_41114",
        ],
    },

    {
        "query":
            "What is the status of the Advanced Software "
            "Development allocation and who is assigned to teach it?",

        "relevant_chunk_ids": [
            "student2_allocation_4",
            "student2_subject_allocation_summary_41114",
        ],
    },

    {
        "query":
            "What is the capacity and room type of "
            "classroom CB10.02.301?",

        "relevant_chunk_ids": [
            "student2_classroom_CB10.02.301",
        ],
    },

    {
        "query":
            "How many subjects, subject offers, classrooms "
            "and teaching allocations are currently tracked?",

        "relevant_chunk_ids": [
            "student2_summary",
        ],
    },
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
    {
        "query": "What grants and publications are attached to the Financial Risk Modelling with AI project?",
        "relevant_keywords": ["Financial Risk Modelling", "Fintech Research Partnership"],
        "expected_relevant": 4,
    },
    {
        "query": "What research project is studying renewable energy on campus?",
        "relevant_keywords": ["Sustainable Campus Energy", "renewable energy"],
        "expected_relevant": 1,
    },
    {
        "query": "What funding body is backing the Sustainable Campus Energy Systems project?",
        "relevant_keywords": ["CSIRO Energy Fund", "Sustainable Campus Energy"],
        "expected_relevant": 2,
    },
    {
        "query": "What publications came out of the AI-Driven Curriculum Analytics project?",
        "relevant_keywords": ["Analysing Curriculum Effectiveness", "AI-Driven Curriculum Analytics"],
        "expected_relevant": 1,
    },
    {
        "query": "What research project uses CNNs for medical diagnosis?",
        "relevant_keywords": ["Diabetic Retinopathy", "Medical Diagnostics"],
        "expected_relevant": 2,
    },
    {
        "query": "What is the status of the Urban Transport Optimisation project?",
        "relevant_keywords": ["Urban Transport Optimisation", "on hold"],
        "expected_relevant": 1,
    },
    {
        "query": "How many research projects, grants and publications does the Research and Grant Management feature track?",
        "relevant_keywords": ["Research and Grant Management feature currently tracks"],
        "expected_relevant": 1,
    },
    {
        "query": "What project is investigating low-cost water purification?",
        "relevant_keywords": ["Renewable Water Purification", "water purification"],
        "expected_relevant": 1,
    },
]


# ============================================================
# Student 5 - Performance & Professional Development
# ============================================================

STUDENT5_BENCHMARKS = [
    {
        "query": "What is the progress and target date of the Strengthen academic leadership development goal?",
        "relevant_chunk_ids": ["student5_goals_1"],
    },
    {
        "query": "Which training program teaches learning analytics and who provides it?",
        "relevant_chunk_ids": ["student5_programs_6"],
    },
    {
        "query": "When did staff ID 8 complete Academic Workload Planning?",
        "relevant_chunk_ids": ["student5_training_8"],
    },
    {
        "query": "What did staff ID 1's performance review say about teaching leadership?",
        "relevant_chunk_ids": ["student5_reviews_1"],
    },
    {
        "query": "What academic leadership recommendation is pending for staff ID 1?",
        "relevant_chunk_ids": ["student5_recommendations_1"],
    },
    {
        "query": "How many performance reviews, development goals and training programs are tracked?",
        "relevant_chunk_ids": ["student5_summary_counts"],
    },
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

    expected_chunk_ids = (
        benchmark.get(
            "relevant_chunk_ids"
        )
    )

    if expected_chunk_ids is not None:
        expected_set = set(
            expected_chunk_ids
        )

        relevant = [
            result
            for result in results
            if result.get(
                "chunk_id"
            )
            in expected_set
        ]

        expected_relevant = len(
            expected_set
        )

    else:
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

        expected_relevant = (
            benchmark[
                "expected_relevant"
            ]
        )

    precision_at_5 = (
        len(relevant)
        / 5
    )

    raw_recall_at_5 = (
        len(relevant)
        / max(
            expected_relevant,
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
