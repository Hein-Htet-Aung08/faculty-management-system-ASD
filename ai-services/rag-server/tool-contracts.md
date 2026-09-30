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

- Source: Student 1 backend/API (`STUDENT1_BACKEND_URL`, default `http://localhost:5001`) — `GET /api/staff`, then per staff member `GET /api/staff/<id>`, `/expertise`, `/qualifications`, `/availability`. The staff database is never read directly.
- Common fields: `feature` = `staff_management`, `student` = `1`, `authority_tier` = `tier_1`.

| Chunk | `chunk_id` / `source_id` | Content |
|---|---|---|
| Staff profile | `student1_staff_<id>` / `student1/staff/<id>` | Name, position, employment type, department, status, expertise (skill level /5), qualifications |
| Availability | `student1_availability_<id>` / `student1/staff/<id>/availability` | Day, time slot and status for each availability entry |
| Department roster | `student1_department_<slug>` / `student1/departments/<slug>` | Staff in the department with position and status |
| Summary | `student1_summary_counts` / `student1/summary` | Total staff, department count, headcount by status |

- Excluded: email and phone (contact details are not needed for grounded answers).
- Failure: if the backend is unreachable, the loader returns `[]` so the shared refresh still succeeds for other features.

## Student 2 - Teaching, Subject & Classroom Allocation

Student 2 contributes subject, subject-offer, classroom and teaching-allocation context through `load_student2_context()`.

TODO: Define Student 2 context sources and chunk contracts.

## Student 3 - Workload & Availability Management

Student 3 contributes workload and availability context through `load_student3_context()`.

TODO: Define Student 3 context sources and chunk contracts.

## Student 4 - Research & Grant Management

Student 4 contributes research and grant context through `load_student4_context()`.

TODO: Adapt existing Release 1 context-loading work to the shared RAG service.

## Student 5 - Performance & Professional Development

Student 5 contributes performance and professional-development context through `load_student5_context()`.

TODO: Define Student 5 context sources and chunk contracts.