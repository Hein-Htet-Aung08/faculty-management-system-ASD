import hashlib
import json
import os
import re
import time
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import requests


# ============================================================
# Common Paths and Configuration
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

PROJECT_ROOT = (
    BASE_DIR
    .parents[1]
)

REPORTS_DIR = (
    PROJECT_ROOT
    / "reports"
)

CORPUS_PATH = (
    BASE_DIR
    / "corpus"
    / "corpus.jsonl"
)

AUDIT_PATH = (
    BASE_DIR
    / "rag-audit.jsonl"
)

CHROMA_PATH = (
    BASE_DIR
    / "chroma"
)

COLLECTION_NAME = (
    "faculty_management_context"
)

EMBED_VECTOR_SIZE = 256


STUDENT1_BACKEND_URL = os.getenv(
    "STUDENT1_BACKEND_URL",
    "http://localhost:5001",
)

STUDENT2_BACKEND_URL = os.getenv(
    "STUDENT2_BACKEND_URL",
    "http://localhost:5002",
)

STUDENT3_BACKEND_URL = os.getenv(
    "STUDENT3_BACKEND_URL",
    "http://localhost:5003",
)

STUDENT4_BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL",
    "http://localhost:5004",
)

STUDENT5_BACKEND_URL = os.getenv(
    "STUDENT5_BACKEND_URL",
    "http://localhost:5005",
)


REPORT_FILES = [
    "run-report.md",
    "integration-report.md",
    "tool-review.md",
    "boundary-analysis.md",
    "rag-report.md",
    "rag-validation-report.md",
]


_collection = None
_last_corpus_chunks = []


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


# ============================================================
# Common Utility Functions
# ============================================================

def now_iso():
    return (
        datetime
        .now(timezone.utc)
        .isoformat()
    )


def tokenize(text):
    tokens = re.findall(
        r"[A-Za-z0-9_]+",
        (text or "").lower(),
    )

    return {
        token
        for token in tokens
        if (
            len(token) > 2
            and token not in STOP_WORDS
        )
    }


def make_chunk(
    *,
    chunk_id,
    source_id,
    authority_tier,
    text,
    feature,
    student,
    metadata=None,
):
    """
    Create one standard RAG chunk.

    All student feature loaders should use this format so that
    citations, confidence calculation and auditing remain consistent.
    """

    return {
        "chunk_id": chunk_id,
        "source_id": source_id,
        "authority_tier": authority_tier,
        "feature": feature,
        "student": student,
        "text": text,
        "metadata": metadata or {},
        "indexed_at": now_iso(),
    }


def call_feature_api(
    method,
    base_url,
    path,
    *,
    params=None,
):
    """
    Shared helper for RAG source loaders.

    Feature context should normally be obtained through the feature's
    backend/API rather than by directly opening another feature's
    database.
    """

    url = (
        f"{base_url.rstrip('/')}"
        f"/{path.lstrip('/')}"
    )

    response = requests.request(
        method=method,
        url=url,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def append_audit(
    tool_name,
    tool_input,
    tool_output,
    validation_status,
    outcome,
    start_time,
):
    AUDIT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    duration_ms = int(
        (time.time() - start_time)
        * 1000
    )

    record = {
        "request_id": str(
            uuid.uuid4()
        ),
        "trace_id": str(
            uuid.uuid4()
        ),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "timestamp": now_iso(),
        "duration_ms": duration_ms,
        "validation_status":
            validation_status,
        "outcome": outcome,
    }

    with AUDIT_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(record)
            + "\n"
        )


def chunk_text(
    text,
    max_words=80,
):
    words = (
        (text or "")
        .split()
    )

    chunks = []

    for index in range(
        0,
        len(words),
        max_words,
    ):
        chunk = " ".join(
            words[
                index:
                index + max_words
            ]
        ).strip()

        if chunk:
            chunks.append(
                chunk
            )

    return chunks


# ============================================================
# Student 1 - Staff Management Context
# ============================================================

def load_student1_context():
    """
    OWNER: Student 1

    Return RAG chunks for Staff Management, sourced from the
    Student 1 backend/API (STUDENT1_BACKEND_URL).

    Chunks produced:
    - one profile per staff member (role, department, status,
      expertise with skill level, qualifications)
    - one availability schedule per staff member
    - one staff roster per department
    - one feature-wide summary of headcounts by status

    Contact details (email, phone) are deliberately excluded.
    Returns [] if the backend is unreachable so one offline
    feature does not break the shared corpus refresh.
    """

    try:
        staff_rows = call_feature_api(
            "GET",
            STUDENT1_BACKEND_URL,
            "/api/staff",
        )

    except requests.RequestException as exc:
        print(
            f"[rag_pipeline] student1 backend unreachable: {exc}"
        )
        return []

    # /api/staff returns one row per staff/expertise pair,
    # so de-duplicate while keeping order.
    staff_ids = list(
        dict.fromkeys(
            row["staff_id"]
            for row in staff_rows
        )
    )

    chunks = []
    departments = {}
    status_counts = {}

    for staff_id in staff_ids:
        try:
            staff = call_feature_api(
                "GET",
                STUDENT1_BACKEND_URL,
                f"/api/staff/{staff_id}",
            )
            expertise = call_feature_api(
                "GET",
                STUDENT1_BACKEND_URL,
                f"/api/staff/{staff_id}/expertise",
            )
            qualifications = call_feature_api(
                "GET",
                STUDENT1_BACKEND_URL,
                f"/api/staff/{staff_id}/qualifications",
            )
            availability = call_feature_api(
                "GET",
                STUDENT1_BACKEND_URL,
                f"/api/staff/{staff_id}/availability",
            )

        except requests.RequestException as exc:
            print(
                f"[rag_pipeline] student1 staff {staff_id} skipped: {exc}"
            )
            continue

        name = staff["name"]
        department = staff["department_name"]

        departments.setdefault(
            department,
            [],
        ).append(
            f"{name} ({staff['position']}, {staff['status']})"
        )

        status_counts[staff["status"]] = (
            status_counts.get(staff["status"], 0)
            + 1
        )

        expertise_text = (
            "; ".join(
                f"{item['expertise_area']} "
                f"(skill level {item['skill_level']}/5)"
                for item in expertise
            )
            or "none recorded"
        )

        qualifications_text = (
            "; ".join(
                f"{item['qualification_name']}, "
                f"{item['institution']} ({item['year_obtained']})"
                for item in qualifications
            )
            or "none recorded"
        )

        chunks.append(
            make_chunk(
                chunk_id=f"student1_staff_{staff_id}",
                source_id=f"student1/staff/{staff_id}",
                authority_tier="tier_1",
                feature="staff_management",
                student=1,
                text=(
                    f"Staff profile: {name} (staff ID {staff_id}) is a "
                    f"{staff['employment_type']} {staff['position']} in the "
                    f"{department} department. "
                    f"Employment status: {staff['status']}. "
                    f"Expertise: {expertise_text}. "
                    f"Qualifications: {qualifications_text}."
                ),
                metadata={
                    "source_type": "staff_profile",
                    "staff_id": staff_id,
                },
            )
        )

        availability_text = (
            "; ".join(
                f"{slot['day']} {slot['time_slot']}: "
                f"{slot['availability_status']}"
                for slot in availability
            )
            or "no availability recorded"
        )

        chunks.append(
            make_chunk(
                chunk_id=f"student1_availability_{staff_id}",
                source_id=f"student1/staff/{staff_id}/availability",
                authority_tier="tier_1",
                feature="staff_management",
                student=1,
                text=(
                    f"Staff availability for {name} ({staff['position']}, "
                    f"{department}): {availability_text}."
                ),
                metadata={
                    "source_type": "staff_availability",
                    "staff_id": staff_id,
                },
            )
        )

    for department, members in departments.items():
        slug = re.sub(
            r"[^a-z0-9]+",
            "_",
            department.lower(),
        ).strip("_")

        chunks.append(
            make_chunk(
                chunk_id=f"student1_department_{slug}",
                source_id=f"student1/departments/{slug}",
                authority_tier="tier_1",
                feature="staff_management",
                student=1,
                text=(
                    f"The {department} department has {len(members)} "
                    f"staff member(s): {', '.join(members)}."
                ),
                metadata={
                    "source_type": "department_roster",
                    "department": department,
                },
            )
        )

    status_text = (
        ", ".join(
            f"{count} {status}"
            for status, count in sorted(status_counts.items())
        )
        or "no staff recorded"
    )

    chunks.append(
        make_chunk(
            chunk_id="student1_summary_counts",
            source_id="student1/summary",
            authority_tier="tier_1",
            feature="staff_management",
            student=1,
            text=(
                f"The Staff Management feature currently records "
                f"{len(staff_ids)} staff member(s) across "
                f"{len(departments)} department(s). "
                f"Staff by employment status: {status_text}."
            ),
            metadata={
                "source_type": "summary",
            },
        )
    )

    return chunks


# ============================================================
# Student 2 - Teaching, Subject & Classroom Allocation Context
# ============================================================

def load_student2_context():
    """
    OWNER: Student 2 - Hein

    Return RAG chunks for:
    - subjects
    - subject offers
    - classrooms
    - teaching allocations

    Use Student 2 backend/API data.

    Each returned item should use make_chunk(...).

    TODO:
    Student 2 implementation will be added after the shared
    RAG infrastructure has been merged.
    """

    return []


# ============================================================
# Student 3 - Workload & Availability Context
# ============================================================

def load_student3_context():
    """
    OWNER: Student 3

    Return RAG chunks for Workload and Availability Management.

    Student 3 may adapt existing Release 1 work here.

    Each returned item should use make_chunk(...).
    """

    return []


# ============================================================
# Student 4 - Research & Grant Management Context
# ============================================================

def load_student4_context():
    """
    OWNER: Student 4

    Return RAG chunks for Research and Grant Management.

    Existing Student 4 RAG corpus-loading work can be adapted into
    this section instead of operating as a separate production
    RAG server.

    Each returned item should use make_chunk(...).
    """

    return []


# ============================================================
# Student 5 - Performance & Professional Development Context
# ============================================================

def load_student5_context():
    """
    OWNER: Student 5

    Return RAG chunks for Performance and Professional Development.

    Each returned item should use make_chunk(...).
    """

    return []


# ============================================================
# Common Project Evidence Context
# ============================================================

def load_report_chunks():
    chunks = []

    for name in REPORT_FILES:
        path = (
            REPORTS_DIR
            / name
        )

        if not path.exists():
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if not text.strip():
            continue

        for index, part in enumerate(
            chunk_text(text),
            start=1,
        ):
            chunks.append(
                make_chunk(
                    chunk_id=(
                        f"report_"
                        f"{path.stem}_"
                        f"{index}"
                    ),
                    source_id=(
                        f"reports/{name}"
                    ),
                    authority_tier="tier_2",
                    feature="shared",
                    student=0,
                    text=part,
                    metadata={
                        "source_type":
                            "report",
                        "file":
                            name,
                    },
                )
            )

    return chunks


def load_repository_chunks():
    ignored = {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
        "chroma",
    }

    files = []

    for root, dirs, filenames in os.walk(
        PROJECT_ROOT,
        topdown=True,
        followlinks=False,
    ):
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in ignored
        ]

        for filename in filenames:
            path = (
                Path(root)
                / filename
            )

            try:
                relative_path = (
                    path.relative_to(
                        PROJECT_ROOT
                    )
                )

            except ValueError:
                continue

            files.append(
                str(relative_path)
                .replace(
                    "\\",
                    "/",
                )
            )

    text = (
        "Repository files include: "
        + ", ".join(
            sorted(files[:400])
        )
    )

    return [
        make_chunk(
            chunk_id=
                "shared_repository_index",
            source_id=
                "repository",
            authority_tier=
                "tier_3",
            feature=
                "shared",
            student=
                0,
            text=
                text,
            metadata={
                "source_type":
                    "repository",
                "file_count":
                    len(files),
            },
        )
    ]


# ============================================================
# Common Corpus Construction
# ============================================================

def build_corpus():
    chunks = []

    chunks.extend(
        load_student1_context()
    )

    chunks.extend(
        load_student2_context()
    )

    chunks.extend(
        load_student3_context()
    )

    chunks.extend(
        load_student4_context()
    )

    chunks.extend(
        load_student5_context()
    )

    chunks.extend(
        load_report_chunks()
    )

    chunks.extend(
        load_repository_chunks()
    )

    return chunks


def write_corpus(chunks):
    CORPUS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with CORPUS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        for chunk in chunks:
            file.write(
                json.dumps(chunk)
                + "\n"
            )


def read_corpus():
    if not CORPUS_PATH.exists():
        return []

    chunks = []

    with CORPUS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                chunks.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:
                continue

    return chunks


# ============================================================
# Common Embedding and Chroma Logic
# ============================================================

def embed_texts(texts):
    vectors = []

    for text in texts:
        values = (
            [0.0]
            * EMBED_VECTOR_SIZE
        )

        tokens = tokenize(
            text
        )

        if not tokens:
            vectors.append(
                values
            )
            continue

        for token in tokens:
            digest = hashlib.sha256(
                token.encode(
                    "utf-8"
                )
            ).digest()

            for index, byte in enumerate(
                digest
            ):
                vector_index = (
                    index
                    % EMBED_VECTOR_SIZE
                )

                values[
                    vector_index
                ] += (
                    byte / 255.0
                ) - 0.5

        norm = (
            sum(
                value * value
                for value in values
            )
            ** 0.5
        )

        if norm > 0:
            values = [
                value / norm
                for value in values
            ]

        vectors.append(
            values
        )

    return vectors


def get_collection():
    global _collection

    if _collection is None:
        client = (
            chromadb
            .PersistentClient(
                path=str(
                    CHROMA_PATH
                )
            )
        )

        _collection = (
            client
            .get_or_create_collection(
                name=
                    COLLECTION_NAME
            )
        )

    return _collection


def reset_collection():
    global _collection

    client = (
        chromadb
        .PersistentClient(
            path=str(
                CHROMA_PATH
            )
        )
    )

    try:
        client.delete_collection(
            name=
                COLLECTION_NAME
        )

    except Exception:
        pass

    _collection = (
        client
        .get_or_create_collection(
            name=
                COLLECTION_NAME
        )
    )


# ============================================================
# Common RAG Tool - Refresh Corpus
# ============================================================

def refresh_corpus(
    caller="student",
):
    global _last_corpus_chunks

    start_time = (
        time.time()
    )

    try:
        chunks = (
            build_corpus()
        )

        _last_corpus_chunks = (
            chunks
        )

        write_corpus(
            chunks
        )

        vector_store_status = (
            "ready"
        )

        vector_store_error = None

        try:
            reset_collection()

            collection = (
                get_collection()
            )

            if chunks:
                ids = [
                    chunk["chunk_id"]
                    for chunk in chunks
                ]

                documents = [
                    chunk["text"]
                    for chunk in chunks
                ]

                metadata = [
                    {
                        "source_id":
                            chunk[
                                "source_id"
                            ],
                        "authority_tier":
                            chunk[
                                "authority_tier"
                            ],
                        "feature":
                            chunk[
                                "feature"
                            ],
                        "student":
                            str(
                                chunk[
                                    "student"
                                ]
                            ),
                        "indexed_at":
                            chunk[
                                "indexed_at"
                            ],
                    }
                    for chunk in chunks
                ]

                embeddings = (
                    embed_texts(
                        documents
                    )
                )

                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadata,
                    embeddings=embeddings,
                )

        except Exception as exc:
            vector_store_status = (
                "degraded"
            )

            vector_store_error = (
                str(exc)
            )

        output = {
            "status":
                "success",
            "caller":
                caller,
            "chunk_count":
                len(chunks),
            "collection":
                COLLECTION_NAME,
            "corpus_path":
                str(CORPUS_PATH),
            "vector_store_status":
                vector_store_status,
        }

        if vector_store_error:
            output[
                "vector_store_error"
            ] = vector_store_error

        append_audit(
            "refresh_corpus",
            {
                "caller":
                    caller,
            },
            output,
            "pass",
            "corpus_refreshed",
            start_time,
        )

        return output

    except Exception as exc:
        output = {
            "status":
                "error",
            "error":
                str(exc),
        }

        append_audit(
            "refresh_corpus",
            {
                "caller":
                    caller,
            },
            output,
            "fail",
            "error",
            start_time,
        )

        return output


# ============================================================
# Common RAG Tool - Retrieve Context
# ============================================================

def lexical_fallback_retrieve(
    query,
    k,
):
    corpus = (
        _last_corpus_chunks
        or read_corpus()
    )

    query_tokens = (
        tokenize(query)
    )

    tier_weight = {
        "tier_1": 3,
        "tier_2": 2,
        "tier_3": 1,
    }

    scored = []

    for chunk in corpus:
        text = (
            chunk.get(
                "text",
                "",
            )
        )

        text_tokens = (
            tokenize(text)
        )

        overlap = len(
            query_tokens
            .intersection(
                text_tokens
            )
        )

        if overlap == 0:
            continue

        scored.append(
            {
                "rank": 0,
                "chunk_id":
                    chunk.get(
                        "chunk_id"
                    ),
                "source_id":
                    chunk.get(
                        "source_id"
                    ),
                "authority_tier":
                    chunk.get(
                        "authority_tier"
                    ),
                "feature":
                    chunk.get(
                        "feature"
                    ),
                "student":
                    chunk.get(
                        "student"
                    ),
                "distance":
                    None,
                "text":
                    text,
                "_score":
                    overlap,
            }
        )

    scored.sort(
        key=lambda row: (
            row.get(
                "_score",
                0,
            ),
            tier_weight.get(
                row.get(
                    "authority_tier"
                ),
                0,
            ),
        ),
        reverse=True,
    )

    top = scored[
        :max(k, 1)
    ]

    for index, row in enumerate(
        top,
        start=1,
    ):
        row["rank"] = (
            index
        )

        row.pop(
            "_score",
            None,
        )

    return top


def retrieve_context(
    query,
    k=5,
    caller="student",
):
    start_time = (
        time.time()
    )

    query = (
        str(query or "")
        .strip()
    )

    if not query:
        return {
            "status":
                "error",
            "error":
                "query is required",
        }

    try:
        k = int(k)

    except (
        TypeError,
        ValueError,
    ):
        k = 5

    k = max(
        1,
        min(
            k,
            20,
        ),
    )

    try:
        retrieval_mode = (
            "vector"
        )

        ranked = []

        try:
            collection = (
                get_collection()
            )

            if (
                collection.count()
                == 0
            ):
                refreshed = (
                    refresh_corpus(
                        caller=
                            "auto_refresh"
                    )
                )

                if (
                    refreshed.get(
                        "status"
                    )
                    != "success"
                ):
                    raise RuntimeError(
                        "corpus unavailable"
                    )

            count = (
                collection.count()
            )

            if count > 0:
                result_count = min(
                    k,
                    count,
                )

                query_embedding = (
                    embed_texts(
                        [query]
                    )
                )

                results = (
                    collection.query(
                        query_embeddings=
                            query_embedding,
                        n_results=
                            result_count,
                    )
                )

                ids = (
                    results.get(
                        "ids"
                    )
                    or [[]]
                )[0]

                documents = (
                    results.get(
                        "documents"
                    )
                    or [[]]
                )[0]

                metadata = (
                    results.get(
                        "metadatas"
                    )
                    or [[]]
                )[0]

                distances = (
                    results.get(
                        "distances"
                    )
                    or [[]]
                )[0]

                query_tokens = (
                    tokenize(query)
                )

                for index, chunk_id in enumerate(
                    ids
                ):
                    document = (
                        documents[index]
                        if index
                        < len(documents)
                        else ""
                    )

                    # Explicit relevance gate.
                    # This supports the Release 1 requirement to
                    # return insufficient context instead of forcing
                    # an unrelated answer.
                    if not (
                        query_tokens
                        .intersection(
                            tokenize(
                                document
                            )
                        )
                    ):
                        continue

                    row_metadata = (
                        metadata[index]
                        if (
                            index
                            < len(metadata)
                            and isinstance(
                                metadata[index],
                                dict,
                            )
                        )
                        else {}
                    )

                    ranked.append(
                        {
                            "rank":
                                len(ranked)
                                + 1,
                            "chunk_id":
                                chunk_id,
                            "source_id":
                                row_metadata.get(
                                    "source_id"
                                ),
                            "authority_tier":
                                row_metadata.get(
                                    "authority_tier"
                                ),
                            "feature":
                                row_metadata.get(
                                    "feature"
                                ),
                            "student":
                                row_metadata.get(
                                    "student"
                                ),
                            "distance":
                                (
                                    distances[
                                        index
                                    ]
                                    if index
                                    < len(distances)
                                    else None
                                ),
                            "text":
                                document,
                        }
                    )

        except Exception:
            retrieval_mode = (
                "lexical_fallback"
            )

            if (
                not _last_corpus_chunks
                and not CORPUS_PATH.exists()
            ):
                refreshed = (
                    refresh_corpus(
                        caller=
                            "auto_refresh"
                    )
                )

                if (
                    refreshed.get(
                        "status"
                    )
                    != "success"
                ):
                    return {
                        "status":
                            "error",
                        "error":
                            "corpus_unavailable",
                    }

            ranked = (
                lexical_fallback_retrieve(
                    query,
                    k,
                )
            )

        output = {
            "status":
                "success",
            "query":
                query,
            "caller":
                caller,
            "k":
                k,
            "retrieval_mode":
                retrieval_mode,
            "results":
                ranked,
        }

        append_audit(
            "retrieve_context",
            {
                "query":
                    query,
                "k":
                    k,
                "caller":
                    caller,
            },
            {
                "result_count":
                    len(ranked),
                "chunk_ids":
                    [
                        row.get(
                            "chunk_id"
                        )
                        for row
                        in ranked
                    ],
            },
            "pass",
            "context_retrieved",
            start_time,
        )

        return output

    except Exception as exc:
        output = {
            "status":
                "error",
            "query":
                query,
            "error":
                str(exc),
        }

        append_audit(
            "retrieve_context",
            {
                "query":
                    query,
                "k":
                    k,
                "caller":
                    caller,
            },
            output,
            "fail",
            "error",
            start_time,
        )

        return output


# ============================================================
# Common Confidence Calculation
# ============================================================

def confidence_from_results(
    results,
):
    if not results:
        return "Unknown"

    tier_1 = sum(
        1
        for result in results
        if result.get(
            "authority_tier"
        )
        == "tier_1"
    )

    tier_2 = sum(
        1
        for result in results
        if result.get(
            "authority_tier"
        )
        == "tier_2"
    )

    if (
        tier_1 >= 2
        and len(results) >= 3
    ):
        return "High"

    if (
        tier_1 >= 1
        or tier_2 >= 2
    ):
        return "Medium"

    return "Low"


# ============================================================
# Common Grounded Generation
# ============================================================

def generate_with_ollama(
    query,
    results,
):
    model_name = os.getenv(
        "OLLAMA_MODEL",
        "qwen2.5:0.5b",
    )

    ollama_generate_url = os.getenv(
        "OLLAMA_GENERATE_URL",
        "http://localhost:11434/api/generate",
    )

    context_parts = []

    for result in results:
        context_parts.append(
            (
                f"[{result.get('source_id')}] "
                f"{result.get('text', '')}"
            )
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are a retrieval-grounded assistant for a Faculty Management System.

Use ONLY the supplied context.

Do not invent facts.
Do not use outside knowledge.

If the context does not contain enough evidence to answer the question, return exactly:

Insufficient context.

QUESTION:
{query}

CONTEXT:
{context}

Return a concise grounded answer.
""".strip()

    try:
        response = requests.post(
            ollama_generate_url,
            json={
                "model":
                    model_name,
                "prompt":
                    prompt,
                "stream":
                    False,
            },
            timeout=120,
        )

        response.raise_for_status()

        answer = (
            response
            .json()
            .get(
                "response",
                "",
            )
            .strip()
        )

        if not answer:
            answer = (
                "Insufficient context."
            )

        return (
            answer,
            None,
        )

    except Exception as exc:
        return (
            None,
            str(exc),
        )


# ============================================================
# Common RAG Tool - Answer Question
# ============================================================

def answer_question(
    query,
    k=5,
    caller="student",
):
    start_time = (
        time.time()
    )

    retrieval = (
        retrieve_context(
            query=query,
            k=k,
            caller=caller,
        )
    )

    if (
        retrieval.get(
            "status"
        )
        != "success"
    ):
        output = {
            "status":
                "error",
            "query":
                query,
            "error":
                retrieval.get(
                    "error",
                    "retrieval_failed",
                ),
        }

        append_audit(
            "answer_question",
            {
                "query":
                    query,
                "k":
                    k,
                "caller":
                    caller,
            },
            output,
            "fail",
            "retrieval_failed",
            start_time,
        )

        return output

    results = (
        retrieval.get(
            "results",
            [],
        )
    )

    if not results:
        output = {
            "status":
                "success",
            "query":
                query,
            "answer":
                "Insufficient context.",
            "citations":
                [],
            "confidence_category":
                "Unknown",
            "retrieval_summary": {
                "k":
                    k,
                "retrieved_count":
                    0,
                "top_chunk":
                    None,
            },
        }

        append_audit(
            "answer_question",
            {
                "query":
                    query,
                "k":
                    k,
                "caller":
                    caller,
            },
            output,
            "pass",
            "insufficient_context",
            start_time,
        )

        return output

    answer, generation_error = (
        generate_with_ollama(
            query,
            results,
        )
    )

    citations = [
        {
            "chunk_id":
                result.get(
                    "chunk_id"
                ),
            "source_id":
                result.get(
                    "source_id"
                ),
            "authority_tier":
                result.get(
                    "authority_tier"
                ),
            "feature":
                result.get(
                    "feature"
                ),
            "student":
                result.get(
                    "student"
                ),
        }
        for result in results
    ]

    confidence = (
        confidence_from_results(
            results
        )
    )

    if generation_error:
        output = {
            "status":
                "error",
            "query":
                query,
            "error":
                "local_model_unavailable",
            "details":
                generation_error,
            "citations":
                citations,
            "confidence_category":
                confidence,
        }

        append_audit(
            "answer_question",
            {
                "query":
                    query,
                "k":
                    k,
                "caller":
                    caller,
            },
            output,
            "fail",
            "generation_failed",
            start_time,
        )

        return output

    output = {
        "status":
            "success",
        "query":
            query,
        "answer":
            answer,
        "citations":
            citations,
        "confidence_category":
            confidence,
        "retrieval_summary": {
            "k":
                k,
            "retrieved_count":
                len(results),
            "top_chunk":
                (
                    results[0]
                    .get(
                        "chunk_id"
                    )
                    if results
                    else None
                ),
        },
    }

    append_audit(
        "answer_question",
        {
            "query":
                query,
            "k":
                k,
            "caller":
                caller,
        },
        {
            "confidence_category":
                confidence,
            "citation_count":
                len(citations),
        },
        "pass",
        "answer_generated",
        start_time,
    )

    return output


# ============================================================
# Local Manual Validation
# ============================================================

if __name__ == "__main__":
    print(
        json.dumps(
            refresh_corpus(),
            indent=2,
        )
    )