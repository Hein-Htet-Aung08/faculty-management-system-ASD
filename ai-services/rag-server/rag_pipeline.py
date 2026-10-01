import hashlib
import json
import math
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

IDF_PATH = (
    BASE_DIR
    / "corpus"
    / "idf.json"
)

COLLECTION_NAME = (
    "faculty_management_context"
)

EMBED_VECTOR_SIZE = 1024


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
_idf = None


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


def tokenize_ordered(text):
    tokens = re.findall(
        r"[A-Za-z0-9_]+",
        (text or "").lower(),
    )

    return [
        token
        for token in tokens
        if (
            len(token) > 2
            and token not in STOP_WORDS
        )
    ]


def bigrams(text):
    words = tokenize_ordered(text)

    return [
        f"{words[index]}_{words[index + 1]}"
        for index in range(len(words) - 1)
    ]


def compute_idf(chunks):
    """
    Document-frequency-weighted term importance across the corpus,
    so rare, topic-specific words (e.g. a project title) count for
    more in similarity scoring than common ones (e.g. "project").
    Without this, a short irrelevant chunk that happens to share a
    few common words with the query can outrank the genuinely
    relevant one.
    """

    document_count = len(chunks) or 1
    document_frequency = {}

    for chunk in chunks:
        for token in tokenize(chunk.get("text", "")):
            document_frequency[token] = (
                document_frequency.get(token, 0) + 1
            )

    return {
        token: math.log((1 + document_count) / (1 + df)) + 1.0
        for token, df in document_frequency.items()
    }


def load_idf():
    global _idf

    if _idf is not None:
        return _idf

    if IDF_PATH.exists():
        try:
            _idf = json.loads(
                IDF_PATH.read_text(encoding="utf-8")
            )
            return _idf
        except (json.JSONDecodeError, OSError):
            pass

    _idf = {}
    return _idf


def write_idf(idf):
    global _idf

    _idf = idf

    IDF_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    IDF_PATH.write_text(
        json.dumps(idf),
        encoding="utf-8",
    )


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

    Return RAG chunks for Staff Management.

    Each returned item should follow make_chunk(...).

    Recommended source:
    Student 1 backend/API.

    TODO:
    Replace this empty list with Student 1 feature context.
    """

    return []


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

    Return RAG chunks for Workload and Availability Management, sourced
    from the Student 3 backend/API (STUDENT3_BACKEND_URL) rather than
    its database directly.
    """

    chunks = []

    try:
        profiles = call_feature_api(
            "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/profiles"
        )
    except requests.RequestException as exc:
        print(f"[rag_pipeline] student3 backend unreachable: {exc}")
        return chunks

    chunks.append(
        make_chunk(
            chunk_id="student3_summary_counts",
            source_id="student3/summary",
            authority_tier="tier_1",
            feature="workload_and_availability_management",
            student=3,
            text=(
                f"The Workload and Availability Management feature currently "
                f"tracks {len(profiles)} staff workload profile(s)."
            ),
        )
    )

    status_members = {}

    for profile in profiles:
        staff_id = profile.get("staff_id")
        text = (
            f"Staff record: {profile.get('staff_name')} (staff ID {staff_id}), "
            f"department {profile.get('department')}. "
            f"Current workload: {profile.get('current_total_hours')}h of "
            f"{profile.get('max_weekly_hours')}h cap. Status: {profile.get('status')}."
        )
        chunks.append(
            make_chunk(
                chunk_id=f"student3_profile_{staff_id}",
                source_id=f"student3/profiles/{staff_id}",
                authority_tier="tier_1",
                feature="workload_and_availability_management",
                student=3,
                text=text,
            )
        )

        status = profile.get("status")
        if status and profile.get("staff_name"):
            status_members.setdefault(status, []).append(profile["staff_name"])

    # One roster chunk per status, so "which staff are overloaded?" has a
    # single chunk holding the complete answer - otherwise top-k retrieval
    # only ever surfaces a couple of individual profiles. Names only, kept
    # short: extra words dilute its similarity against single-person chunks
    # (same lesson as the Student 1 status rosters above).
    for status, members in sorted(status_members.items()):
        slug = re.sub(r"[^a-z0-9]+", "_", status.lower()).strip("_")
        chunks.append(
            make_chunk(
                chunk_id=f"student3_status_{slug}",
                source_id=f"student3/status/{slug}",
                authority_tier="tier_1",
                feature="workload_and_availability_management",
                student=3,
                text=f"{status} staff roster ({len(members)}): {', '.join(members)}.",
                metadata={"source_type": "status_roster", "status": status},
            )
        )

    try:
        alerts = call_feature_api(
            "GET", STUDENT3_BACKEND_URL, "/api/staff-workload/alerts", params={"status": "open"}
        )
    except requests.RequestException:
        alerts = []

    for alert in alerts:
        text = (
            f"Open workload alert for staff ID {alert.get('staff_id')}: "
            f"{alert.get('alert_type')} - {alert.get('message')}."
        )
        chunks.append(
            make_chunk(
                chunk_id=f"student3_alert_{alert.get('alert_id')}",
                source_id=f"student3/alerts/{alert.get('alert_id')}",
                authority_tier="tier_1",
                feature="workload_and_availability_management",
                student=3,
                text=text,
            )
        )

    return chunks


# ============================================================
# Student 4 - Research & Grant Management Context
# ============================================================

def _student4_resolve_staff(staff_id, cache):
    if staff_id is None:
        return "unassigned"

    if staff_id in cache:
        return cache[staff_id]

    display = f"staff ID {staff_id} (name unavailable)"

    try:
        staff = call_feature_api(
            "GET",
            STUDENT1_BACKEND_URL,
            f"/api/staff/{staff_id}",
        )
        name = staff.get("name")
        if name:
            display = f"{name} (staff ID {staff_id})"
    except requests.RequestException:
        pass

    cache[staff_id] = display
    return display


def load_student4_context():
    """
    OWNER: Student 4

    Return RAG chunks for Research and Grant Management, sourced from
    the Student 4 backend/API (STUDENT4_BACKEND_URL) rather than its
    database directly.
    """

    chunks = []

    try:
        projects = call_feature_api("GET", STUDENT4_BACKEND_URL, "/projects")
    except requests.RequestException as exc:
        print(f"[rag_pipeline] student4 backend unreachable: {exc}")
        return chunks

    staff_cache = {}
    grant_count = 0
    publication_count = 0

    for project in projects:
        project_id = project.get("projectID")
        lead_id = project.get("leadStaffID")
        lead_display = (
            _student4_resolve_staff(lead_id, staff_cache)
            if lead_id is not None
            else "unassigned"
        )

        text = (
            f"Research Project: {project.get('title')}. "
            f"Department: {project.get('department')}. "
            f"Status: {project.get('status')}. "
            f"Lead staff: {lead_display}. "
            f"Start date: {project.get('startDate', 'unspecified')}. "
            f"End date: {project.get('endDate', 'ongoing')}. "
            f"Description: {project.get('description', 'no description provided')}."
        )

        chunks.append(
            make_chunk(
                chunk_id=f"student4_project_{project_id}",
                source_id=f"student4/projects/{project_id}",
                authority_tier="tier_1",
                feature="research_grant_management",
                student=4,
                text=text,
            )
        )

        try:
            grants = call_feature_api(
                "GET", STUDENT4_BACKEND_URL, f"/projects/{project_id}/grants"
            )
        except requests.RequestException:
            grants = []

        for grant in grants:
            grant_count += 1
            awarded = grant.get("amountAwarded")
            text = (
                f"Grant from {grant.get('fundingBody')} for project {project_id} "
                f"({project.get('title')}). "
                f"Amount requested: {grant.get('amountRequested')}. "
                f"Amount awarded: {awarded if awarded is not None else 'not yet awarded'}. "
                f"Application deadline: {grant.get('applicationDeadline')}. "
                f"Status: {grant.get('status')}."
            )
            chunks.append(
                make_chunk(
                    chunk_id=f"student4_grant_{grant.get('grantID')}",
                    source_id=f"student4/grants/{grant.get('grantID')}",
                    authority_tier="tier_1",
                    feature="research_grant_management",
                    student=4,
                    text=text,
                )
            )

        try:
            publications = call_feature_api(
                "GET", STUDENT4_BACKEND_URL, f"/projects/{project_id}/publications"
            )
        except requests.RequestException:
            publications = []

        for publication in publications:
            publication_count += 1
            staff_id = publication.get("staffID")
            staff_display = (
                _student4_resolve_staff(staff_id, staff_cache)
                if staff_id is not None
                else "unspecified"
            )
            text = (
                f"Publication: {publication.get('title')}. "
                f"Linked project: {project.get('title')} (project ID {project_id}). "
                f"Type: {publication.get('publicationType')}. "
                f"Journal/venue: {publication.get('journalOrVenue', 'unspecified')}. "
                f"Date published: {publication.get('datePublished', 'unpublished/pending')}. "
                f"Staff: {staff_display}."
            )
            chunks.append(
                make_chunk(
                    chunk_id=f"student4_publication_{publication.get('publicationID')}",
                    source_id=f"student4/publications/{publication.get('publicationID')}",
                    authority_tier="tier_1",
                    feature="research_grant_management",
                    student=4,
                    text=text,
                )
            )

    chunks.append(
        make_chunk(
            chunk_id="student4_summary_counts",
            source_id="student4/summary",
            authority_tier="tier_1",
            feature="research_grant_management",
            student=4,
            text=(
                f"The Research and Grant Management feature currently tracks "
                f"{len(projects)} research project(s), {grant_count} grant(s), "
                f"and {publication_count} publication(s)."
            ),
        )
    )

    return chunks


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

def _hash_into(values, term, weight):
    digest = hashlib.sha256(
        term.encode("utf-8")
    ).digest()

    for index, byte in enumerate(digest):
        vector_index = index % EMBED_VECTOR_SIZE

        values[vector_index] += (
            ((byte / 255.0) - 0.5) * weight
        )


def embed_texts(texts, idf=None):
    idf = idf or {}
    default_idf = 1.0
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
            _hash_into(
                values,
                token,
                idf.get(token, default_idf),
            )

        # Bigrams carry word-order signal that a bag-of-unigrams
        # loses, at a lower weight since they are a secondary signal.
        for bigram in bigrams(text):
            _hash_into(values, bigram, 0.5)

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

                idf = compute_idf(chunks)
                write_idf(idf)

                embeddings = (
                    embed_texts(
                        documents,
                        idf=idf,
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
                        [query],
                        idf=load_idf(),
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
        # llama3.1:8b generation on a CPU-only box routinely takes
        # 80-130s+; 120s was cutting off slow-but-correct answers.
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
            timeout=240,
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