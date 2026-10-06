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
    "mcp-validation-report.md",
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
    status_members = {}

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
        ).append(name)

        status_members.setdefault(
            staff["status"],
            [],
        ).append(name)

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
                # Names only, kept short: this is the one chunk that
                # answers "who is in X?" in full, and extra words
                # dilute its similarity so single-person chunks
                # outranked it. Avoids "has N staff member(s)", which
                # matched the filler words of most questions.
                text=(
                    f"{department} department roster "
                    f"({len(members)}): {', '.join(members)}."
                ),
                metadata={
                    "source_type": "department_roster",
                    "department": department,
                },
            )
        )

    # One roster per employment status, so "which staff are active /
    # on leave?" has a single chunk holding the complete answer --
    # otherwise top-k retrieval only surfaces a few individual profiles.
    for status, members in sorted(status_members.items()):
        slug = re.sub(
            r"[^a-z0-9]+",
            "_",
            status.lower(),
        ).strip("_")

        chunks.append(
            make_chunk(
                chunk_id=f"student1_status_{slug}",
                source_id=f"student1/status/{slug}",
                authority_tier="tier_1",
                feature="staff_management",
                student=1,
                text=(
                    f"{status} staff roster "
                    f"({len(members)}): {', '.join(members)}."
                ),
                metadata={
                    "source_type": "status_roster",
                    "status": status,
                },
            )
        )

    status_text = (
        ", ".join(
            f"{len(members)} {status}"
            for status, members in sorted(status_members.items())
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
                f"Staff Management totals: {len(staff_ids)} staff "
                f"across {len(departments)} department(s). "
                f"Headcount by employment status: {status_text}."
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

def _student2_resolve_staff(
    staff_id,
    cache,
):
    """
    Resolve a Student 2 allocation staff ID through the
    Student 1 Staff Management backend.

    Staff Management remains the authority for staff identity.
    If that service cannot be reached, preserve the staff ID
    rather than failing the Student 2 RAG corpus refresh.
    """

    if staff_id is None:
        return "unassigned"

    if staff_id in cache:
        return cache[
            staff_id
        ]

    display = (
        f"staff ID {staff_id}"
    )

    try:
        staff = call_feature_api(
            "GET",
            STUDENT1_BACKEND_URL,
            f"/api/staff/{staff_id}",
        )

        name = staff.get(
            "name"
        )

        if name:
            display = (
                f"{name} "
                f"(staff ID {staff_id})"
            )

    except requests.RequestException:
        pass

    cache[
        staff_id
    ] = display

    return display


def load_student2_context():
    """
    OWNER: Student 2 - Hein

    Return RAG chunks for Teaching, Subject & Classroom
    Allocation using data exposed through the Student 2
    feature backend.

    Chunks include:
    - feature summary
    - one chunk per subject
    - one chunk per subject offer
    - one chunk per classroom
    - one chunk per teaching allocation

    The RAG service does not directly access the Student 2
    database.
    """

    chunks = []

    try:
        context = call_feature_api(
            "GET",
            STUDENT2_BACKEND_URL,
            "/api/rag/context",
        )

    except requests.RequestException as exc:
        print(
            "[rag_pipeline] "
            "student2 backend unreachable: "
            f"{exc}"
        )

        return chunks

    subjects = context.get(
        "subjects",
        [],
    )

    offers = context.get(
        "subject_offers",
        [],
    )

    classrooms = context.get(
        "classrooms",
        [],
    )

    allocations = context.get(
        "teaching_allocations",
        [],
    )

    subject_by_code = {
        subject.get(
            "subject_code"
        ): subject
        for subject in subjects
    }

    offer_by_id = {
        offer.get(
            "offer_id"
        ): offer
        for offer in offers
    }

    classroom_by_id = {
        classroom.get(
            "classroom_id"
        ): classroom
        for classroom in classrooms
    }

    status_counts = {}

    for allocation in allocations:
        status = allocation.get(
            "allocation_status",
            "UNKNOWN",
        )

        status_counts[
            status
        ] = (
            status_counts.get(
                status,
                0,
            )
            + 1
        )

    status_text = (
        ", ".join(
            f"{count} {status}"
            for (
                status,
                count,
            )
            in sorted(
                status_counts.items()
            )
        )
        or "no allocations recorded"
    )

    chunks.append(
        make_chunk(
            chunk_id=
                "student2_summary",

            source_id=
                "student2/summary",

            authority_tier=
                "tier_1",

            feature=
                "teaching_subject_and_classroom_allocation",

            student=
                2,

            text=(
                "Teaching, Subject & Classroom Allocation "
                f"currently contains {len(subjects)} subject(s), "
                f"{len(offers)} subject offer(s), "
                f"{len(classrooms)} classroom(s), and "
                f"{len(allocations)} teaching allocation(s). "
                "Teaching allocation status counts: "
                f"{status_text}."
            ),

            metadata={
                "source_type":
                    "summary",
            },
        )
    )


    # --------------------------------------------------------
    # Subjects
    # --------------------------------------------------------

    for subject in subjects:
        subject_code = subject.get(
            "subject_code"
        )

        subject_name = subject.get(
            "name"
        )

        required_expertise = (
            subject.get(
                "required_expertise"
            )
            or "none recorded"
        )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_subject_"
                    f"{subject_code}"
                ),

                source_id=(
                    "student2/subjects/"
                    f"{subject_code}"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Subject {subject_code} is "
                    f"{subject_name}. "
                    "Required teaching expertise: "
                    f"{required_expertise}."
                ),

                metadata={
                    "source_type":
                        "subject",

                    "subject_code":
                        subject_code,
                },
            )
        )


    # --------------------------------------------------------
    # Subject Offers
    # --------------------------------------------------------

    for offer in offers:
        offer_id = offer.get(
            "offer_id"
        )

        subject_code = offer.get(
            "subject_code"
        )

        subject = subject_by_code.get(
            subject_code,
            {},
        )

        subject_name = (
            subject.get(
                "name"
            )
            or "unknown subject"
        )

        required_expertise = (
            subject.get(
                "required_expertise"
            )
            or "none recorded"
        )

        semester = offer.get(
            "semester"
        )

        year = offer.get(
            "year"
        )

        expected_enrollment = (
            offer.get(
                "expected_enrollment"
            )
        )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_offer_"
                    f"{offer_id}"
                ),

                source_id=(
                    "student2/subject-offers/"
                    f"{offer_id}"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Subject offer {offer_id} is "
                    f"{subject_name} "
                    f"(subject {subject_code}). "
                    f"It is offered in semester {semester} "
                    f"{year}. "
                    f"Expected enrollment: "
                    f"{expected_enrollment} students. "
                    f"Required teaching expertise for "
                    f"{subject_name}: "
                    f"{required_expertise}."
                ),

                metadata={
                    "source_type":
                        "subject_offer",

                    "offer_id":
                        offer_id,

                    "subject_code":
                        subject_code,
                },
            )
        )

    # --------------------------------------------------------
    # Classrooms
    # --------------------------------------------------------

    for classroom in classrooms:
        classroom_id = classroom.get(
            "classroom_id"
        )

        building = classroom.get(
            "building"
        )

        floor = classroom.get(
            "floor"
        )

        room_number = classroom.get(
            "room_number"
        )

        capacity = classroom.get(
            "capacity"
        )

        room_type = classroom.get(
            "room_type"
        )

        facilities = (
            classroom.get(
                "facilities"
            )
            or "none recorded"
        )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_classroom_"
                    f"{classroom_id}"
                ),

                source_id=(
                    "student2/classrooms/"
                    f"{classroom_id}"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Classroom {classroom_id} is in "
                    f"building {building}, floor {floor}, "
                    f"room {room_number}. "
                    f"Room type: {room_type}. "
                    f"Capacity: {capacity} students. "
                    f"Facilities: {facilities}."
                ),

                metadata={
                    "source_type":
                        "classroom",

                    "classroom_id":
                        classroom_id,
                },
            )
        )


    # --------------------------------------------------------
    # Teaching Allocations
    # --------------------------------------------------------

    staff_cache = {}

    for allocation in allocations:
        allocation_id = allocation.get(
            "allocation_id"
        )

        offer_id = allocation.get(
            "offer_id"
        )

        classroom_id = allocation.get(
            "classroom_id"
        )

        offer = offer_by_id.get(
            offer_id,
            {},
        )

        subject_code = offer.get(
            "subject_code"
        )

        subject = subject_by_code.get(
            subject_code,
            {},
        )

        subject_name = (
            subject.get(
                "name"
            )
            or "unknown subject"
        )

        required_expertise = (
            subject.get(
                "required_expertise"
            )
            or "none recorded"
        )

        semester = (
            offer.get(
                "semester"
            )
            or "unknown semester"
        )

        year = (
            offer.get(
                "year"
            )
            or "unknown year"
        )

        expected_enrollment = (
            offer.get(
                "expected_enrollment"
            )
        )

        classroom = classroom_by_id.get(
            classroom_id,
            {},
        )

        assigned_staff = (
            _student2_resolve_staff(
                allocation.get(
                    "assigned_staff_member"
                ),
                staff_cache,
            )
        )

        classroom_type = (
            classroom.get(
                "room_type"
            )
            or "unknown room type"
        )

        classroom_capacity = (
            classroom.get(
                "capacity"
            )
        )

        classroom_facilities = (
            classroom.get(
                "facilities"
            )
            or "none recorded"
        )

        classroom_building = (
            classroom.get(
                "building"
            )
            or "unknown building"
        )

        classroom_floor = (
            classroom.get(
                "floor"
            )
            or "unknown floor"
        )

        classroom_room_number = (
            classroom.get(
                "room_number"
            )
            or "unknown room"
        )

        expected_class_size = (
            allocation.get(
                "expected_class_size"
            )
        )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_allocation_"
                    f"{allocation_id}"
                ),

                source_id=(
                    "student2/teaching-allocations/"
                    f"{allocation_id}"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Teaching allocation {allocation_id}. "

                    f"Subject: {subject_name} "
                    f"(subject {subject_code}). "

                    f"Subject offer: {offer_id}, "
                    f"semester {semester} {year}, "
                    f"expected enrollment "
                    f"{expected_enrollment} students. "

                    f"Required teaching expertise: "
                    f"{required_expertise}. "

                    f"Assigned staff: "
                    f"{assigned_staff}. "

                    f"Classroom: {classroom_id}, "
                    f"{classroom_type}, "
                    f"building {classroom_building}, "
                    f"floor {classroom_floor}, "
                    f"room {classroom_room_number}. "

                    f"Classroom capacity: "
                    f"{classroom_capacity} students. "

                    f"Classroom facilities: "
                    f"{classroom_facilities}. "

                    f"Teaching session schedule: "
                    f"{allocation.get('day')} "
                    f"{allocation.get('date_range')}, "
                    f"{allocation.get('start_time')} to "
                    f"{allocation.get('end_time')}. "

                    f"Class type: "
                    f"{allocation.get('class_type')}. "

                    f"Expected class size: "
                    f"{expected_class_size} students. "

                    f"Allocation status: "
                    f"{allocation.get('allocation_status')}."
                ),

                metadata={
                    "source_type":
                        "teaching_allocation",

                    "allocation_id":
                        allocation_id,

                    "offer_id":
                        offer_id,

                    "subject_code":
                        subject_code,

                    "classroom_id":
                        classroom_id,
                },
            )
        )

    # --------------------------------------------------------
    # Classroom Allocation Summaries
    # --------------------------------------------------------

    allocations_by_classroom = {}

    for allocation in allocations:
        classroom_id = (
            allocation.get(
                "classroom_id"
            )
        )

        if not classroom_id:
            continue

        if (
            allocation.get(
                "allocation_status"
            )
            == "CANCELLED"
        ):
            continue

        allocations_by_classroom.setdefault(
            classroom_id,
            [],
        ).append(
            allocation
        )


    for (
        classroom_id,
        classroom_allocations,
    ) in allocations_by_classroom.items():

        classroom = (
            classroom_by_id.get(
                classroom_id,
                {},
            )
        )

        schedule_descriptions = []

        for allocation in classroom_allocations:
            allocation_id = (
                allocation.get(
                    "allocation_id"
                )
            )

            offer_id = (
                allocation.get(
                    "offer_id"
                )
            )

            offer = (
                offer_by_id.get(
                    offer_id,
                    {},
                )
            )

            subject_code = (
                offer.get(
                    "subject_code"
                )
            )

            subject = (
                subject_by_code.get(
                    subject_code,
                    {},
                )
            )

            subject_name = (
                subject.get(
                    "name"
                )
                or "unknown subject"
            )

            schedule_descriptions.append(
                (
                    f"Teaching allocation {allocation_id} "
                    f"for {subject_name} "
                    f"(subject {subject_code}) "
                    f"uses classroom {classroom_id} on "
                    f"{allocation.get('day')} "
                    f"during {allocation.get('date_range')} "
                    f"{offer.get('year')}, "
                    f"from {allocation.get('start_time')} "
                    f"to {allocation.get('end_time')}. "
                    f"Therefore classroom {classroom_id} "
                    f"is unavailable for another teaching "
                    f"allocation during that scheduled time. "
                    f"Allocation status: "
                    f"{allocation.get('allocation_status')}."
                )
            )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_classroom_allocation_summary_"
                    f"{classroom_id}"
                ),

                source_id=(
                    "student2/classrooms/"
                    f"{classroom_id}/allocations"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Classroom allocation schedule for "
                    f"{classroom_id}. "
                    f"Room type: "
                    f"{classroom.get('room_type')}. "
                    f"Capacity: "
                    f"{classroom.get('capacity')} students. "
                    f"This classroom has "
                    f"{len(classroom_allocations)} "
                    f"non-cancelled teaching allocation(s). "
                    + " ".join(
                        schedule_descriptions
                    )
                ),

                metadata={
                    "source_type":
                        "classroom_allocation_summary",

                    "classroom_id":
                        classroom_id,

                    "allocation_count":
                        len(
                            classroom_allocations
                        ),
                },
            )
        )

    # --------------------------------------------------------
    # Subject Allocation Summaries
    # --------------------------------------------------------

    allocations_by_subject = {}

    for allocation in allocations:
        offer_id = allocation.get(
            "offer_id"
        )

        offer = offer_by_id.get(
            offer_id,
            {},
        )

        subject_code = offer.get(
            "subject_code"
        )

        if not subject_code:
            continue

        allocations_by_subject.setdefault(
            subject_code,
            [],
        ).append(
            allocation
        )


    for (
        subject_code,
        subject_allocations,
    ) in allocations_by_subject.items():

        subject = subject_by_code.get(
            subject_code,
            {},
        )

        subject_name = (
            subject.get(
                "name"
            )
            or "unknown subject"
        )

        required_expertise = (
            subject.get(
                "required_expertise"
            )
            or "none recorded"
        )

        allocation_descriptions = []

        for allocation in subject_allocations:
            allocation_id = (
                allocation.get(
                    "allocation_id"
                )
            )

            offer_id = (
                allocation.get(
                    "offer_id"
                )
            )

            offer = offer_by_id.get(
                offer_id,
                {},
            )

            classroom_id = (
                allocation.get(
                    "classroom_id"
                )
            )

            classroom = (
                classroom_by_id.get(
                    classroom_id,
                    {},
                )
            )

            assigned_staff = (
                _student2_resolve_staff(
                    allocation.get(
                        "assigned_staff_member"
                    ),
                    staff_cache,
                )
            )

            room_type = (
                classroom.get(
                    "room_type"
                )
                or "unknown room type"
            )

            capacity = (
                classroom.get(
                    "capacity"
                )
            )

            facilities = (
                classroom.get(
                    "facilities"
                )
                or "none recorded"
            )

            expected_enrollment = (
                offer.get(
                    "expected_enrollment"
                )
            )

            allocation_descriptions.append(
                (
                    f"Allocation {allocation_id}: "
                    f"offer {offer_id}, "
                    f"semester {offer.get('semester')} "
                    f"{offer.get('year')}, "
                    f"expected enrollment "
                    f"{expected_enrollment}; "
                    f"classroom {classroom_id}, "
                    f"{room_type}, "
                    f"capacity {capacity}, "
                    f"facilities {facilities}; "
                    f"schedule "
                    f"{allocation.get('day')} "
                    f"{allocation.get('date_range')} "
                    f"{allocation.get('start_time')} to "
                    f"{allocation.get('end_time')}; "
                    f"class type "
                    f"{allocation.get('class_type')}; "
                    f"expected class size "
                    f"{allocation.get('expected_class_size')}; "
                    f"assigned staff {assigned_staff}; "
                    f"status "
                    f"{allocation.get('allocation_status')}."
                )
            )

        chunks.append(
            make_chunk(
                chunk_id=(
                    "student2_subject_allocation_summary_"
                    f"{subject_code}"
                ),

                source_id=(
                    "student2/subjects/"
                    f"{subject_code}/allocations"
                ),

                authority_tier=
                    "tier_1",

                feature=
                    "teaching_subject_and_classroom_allocation",

                student=
                    2,

                text=(
                    f"Complete teaching allocation summary for "
                    f"{subject_name} "
                    f"(subject {subject_code}). "
                    f"Required teaching expertise: "
                    f"{required_expertise}. "
                    f"This subject has "
                    f"{len(subject_allocations)} "
                    f"teaching allocation(s). "
                    + " ".join(
                        allocation_descriptions
                    )
                ),

                metadata={
                    "source_type":
                        "subject_allocation_summary",

                    "subject_code":
                        subject_code,

                    "allocation_count":
                        len(
                            subject_allocations
                        ),
                },
            )
        )

    return chunks


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
    resources = {
        "reviews": "performance-reviews",
        "goals": "development-goals",
        "programs": "training-programs",
        "training": "staff-training",
        "recommendations": "development-recommendations",
    }
    records = {}
    try:
        for name, resource in resources.items():
            rows = call_feature_api("GET", STUDENT5_BACKEND_URL, f"/api/{resource}")
            if not isinstance(rows, list):
                raise ValueError(f"unexpected {resource} response")
            records[name] = rows
    except (requests.RequestException, ValueError) as exc:
        print(f"[rag_pipeline] student5 backend unavailable: {exc}")
        return []

    staff_names = {}
    try:
        directory = call_feature_api("GET", STUDENT5_BACKEND_URL, "/api/integration/staff")
        for staff in directory.get("staff", []):
            if staff.get("staff_id") and staff.get("name"):
                staff_names[staff["staff_id"]] = staff["name"]
    except (requests.RequestException, AttributeError, TypeError):
        pass

    def staff_label(staff_id):
        name = staff_names.get(staff_id)
        return f"{name} (staff ID {staff_id})" if name else f"staff ID {staff_id}"

    def add_chunk(kind, row, key, text, staff_id=None):
        record_id = row[key]
        metadata = {"source_type": kind, "record_id": record_id}
        if staff_id is not None:
            metadata["staff_id"] = staff_id
        return make_chunk(
            chunk_id=f"student5_{kind}_{record_id}",
            source_id=f"student5/{resources[kind]}/{record_id}",
            authority_tier="tier_1",
            feature="performance_professional_development",
            student=5,
            text=text,
            metadata=metadata,
        )

    programs = {row["trainingID"]: row for row in records["programs"]}
    goals = {row["goalID"]: row for row in records["goals"]}
    chunks = []

    for review in records["reviews"]:
        staff_id = review["staffID"]
        rating = review.get("rating")
        chunks.append(add_chunk(
            "reviews", review, "reviewID",
            f"Performance review for {staff_label(staff_id)} on {review['reviewDate']}. "
            f"Reviewer staff ID: {review['reviewerID']}. "
            f"Rating: {f'{rating}/5' if rating is not None else 'not recorded'}. "
            f"Feedback: {review.get('feedback') or 'not recorded'}. "
            f"Review status: {review['status']}.",
            staff_id,
        ))

    for goal in records["goals"]:
        staff_id = goal["staffID"]
        chunks.append(add_chunk(
            "goals", goal, "goalID",
            f"Development goal for {staff_label(staff_id)}: {goal['title']}. "
            f"Description: {goal.get('description') or 'not recorded'}. "
            f"Target date: {goal.get('targetDate') or 'not recorded'}. "
            f"Progress: {goal['progress']}%. Goal status: {goal['status']}.",
            staff_id,
        ))

    for program in records["programs"]:
        chunks.append(add_chunk(
            "programs", program, "trainingID",
            f"Training program: {program['title']}. "
            f"Skill area: {program.get('skillArea') or 'not recorded'}. "
            f"Provider: {program.get('provider') or 'not recorded'}. "
            f"Start date: {program.get('startDate') or 'not recorded'}. "
            f"End date: {program.get('endDate') or 'not recorded'}. "
            f"Description: {program.get('description') or 'not recorded'}.",
        ))

    for enrolment in records["training"]:
        staff_id = enrolment["staffID"]
        program = programs.get(enrolment["trainingID"], {})
        chunks.append(add_chunk(
            "training", enrolment, "staffTrainingID",
            f"Staff training for {staff_label(staff_id)}: "
            f"{program.get('title') or 'program title unavailable'} "
            f"(training ID {enrolment['trainingID']}). "
            f"Enrolment date: {enrolment.get('enrolmentDate') or 'not recorded'}. "
            f"Completion date: {enrolment.get('completionDate') or 'not recorded'}. "
            f"Training status: {enrolment['status']}.",
            staff_id,
        ))

    for recommendation in records["recommendations"]:
        staff_id = recommendation["staffID"]
        goal_id = recommendation.get("goalID")
        goal = goals.get(goal_id, {})
        related_goal = goal.get("title") or (f"goal ID {goal_id}" if goal_id else "none")
        chunks.append(add_chunk(
            "recommendations", recommendation, "recommendationID",
            f"Development recommendation for {staff_label(staff_id)}. "
            f"Type: {recommendation['recommendationType']}. "
            f"Proposed action: {recommendation['recommendation']}. "
            f"Rationale: {recommendation.get('rationale') or 'not recorded'}. "
            f"Related goal: {related_goal}. "
            f"Generated on: {recommendation['dateGenerated']}. "
            f"Decision status: {recommendation['status']}. "
            "A recommendation is not proof that the action was completed.",
            staff_id,
        ))

    staff_ids = {
        row["staffID"] for name in ("reviews", "goals", "training", "recommendations")
        for row in records[name]
    }
    chunks.append(make_chunk(
        chunk_id="student5_summary_counts",
        source_id="student5/summary",
        authority_tier="tier_1",
        feature="performance_professional_development",
        student=5,
        text=(
            "Performance and Professional Development currently tracks "
            f"{len(staff_ids)} staff member(s), {len(records['reviews'])} performance review(s), "
            f"{len(records['goals'])} development goal(s), "
            f"{len(records['programs'])} training program(s), "
            f"{len(records['training'])} staff training record(s), and "
            f"{len(records['recommendations'])} development recommendation(s)."
        ),
        metadata={"source_type": "summary"},
    ))
    return chunks


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
    # Feature hashing: each term maps to ONE bucket across the whole
    # vector, with a +/- sign to cancel collisions on average.
    # (Spreading the 32 digest bytes over `index % size` only ever
    # touched dimensions 0-31, so every term overlapped every other.)
    digest = hashlib.sha256(
        term.encode("utf-8")
    ).digest()

    vector_index = (
        int.from_bytes(digest[:4], "big")
        % EMBED_VECTOR_SIZE
    )

    sign = 1.0 if digest[4] & 1 else -1.0

    values[vector_index] += sign * weight


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
    # llama3.1:8b by default: qwen2.5:0.5b often attributed facts to the
    # wrong staff member or echoed the raw context instead of answering.
    # Same model the agentic loop already uses. Override with OLLAMA_MODEL.
    model_name = os.getenv(
        "OLLAMA_MODEL",
        "llama3.1:8b",
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

        The retrieved context may contain both relevant and irrelevant chunks.

        Identify the evidence that directly relates to the question.
        Ignore retrieved chunks that are unrelated to the entities or relationships
        mentioned in the question.

        You may combine facts from multiple retrieved chunks when the context
        explicitly shows that those facts refer to the same entity or to linked entities.

        Follow relationships only when they are supported by the supplied context.
        Do not invent missing links.
        Do not assume that every retrieved chunk is relevant.
        Do not use outside knowledge.

        If the supplied context contains enough evidence to answer the question,
        provide a concise grounded answer.

        If the question asks who or which (a list), include EVERY matching
        person or item found anywhere in the context, including list or
        roster entries, not only those with their own detailed record.

        If the supplied context does not contain enough evidence to answer the question,
        return exactly:

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
                # Grounded answers should be repeatable, not creative.
                # Ollama's default (0.8) let small models pick a
                # different, wrong name from the same context.
                "options": {
                    "temperature":
                        0,
                },
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
