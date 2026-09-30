# Shared RAG Tool Contracts

The Faculty Management System uses one shared local RAG service.

All student features contribute context to the same shared corpus.

## refresh_corpus

- Purpose: Rebuild the shared corpus and retrieval index.
- Input: `caller` (optional).
- Output: `status`, `chunk_count`, `collection`, `corpus_path`, and vector-store status.
- Policy: Shared index update.

## retrieve_context

- Purpose: Retrieve project context relevant to a query.
- Input: `query`, optional `k`, optional `caller`.
- Output: Ranked `results[]`.
- Each result should contain:
  - `chunk_id`
  - `source_id`
  - `authority_tier`
  - `feature`
  - `student`
  - `text`
- Policy: Read only.

## answer_question

- Purpose: Produce an answer grounded only in retrieved project context.
- Input: `query`, optional `k`, optional `caller`.
- Output:
  - `answer`
  - `citations[]`
  - `confidence_category`
  - `retrieval_summary`
- If relevant context is unavailable, the response must state `Insufficient context.`
- Policy: Read + grounded generation.

---

# Feature Context Responsibilities

## Student 1 - Staff Management

Student 1 contributes Staff Management context through `load_student1_context()` in `rag_pipeline.py`.

TODO: Define Student 1 context sources and chunk contracts.

## Student 2 - Teaching, Subject & Classroom Allocation

Student 2 contributes subject, subject-offer, classroom and teaching-allocation context through `load_student2_context()`.

TODO: Define Student 2 context sources and chunk contracts.

## Student 3 - Workload & Availability Management

Student 3 contributes workload and availability context through `load_student3_context()`.

TODO: Define Student 3 context sources and chunk contracts.

## Student 4 - Research & Grant Management

Student 4 contributes research and grant context through `load_student4_context()`, which reads
from `STUDENT4_BACKEND_URL` (`/projects`, `/projects/<id>/grants`, `/projects/<id>/publications`)
rather than the database directly, and resolves lead/publication staff names via
`STUDENT1_BACKEND_URL`'s `/api/staff/<id>` (degrading to `staff ID <id> (name unavailable)` if
that service is unreachable). Emits one `tier_1` chunk per project, grant and publication, plus a
summary-counts chunk, all tagged `feature="research_grant_management"`, `student=4`.

## Student 5 - Performance & Professional Development

Student 5 contributes performance and professional-development context through `load_student5_context()`.

TODO: Define Student 5 context sources and chunk contracts.