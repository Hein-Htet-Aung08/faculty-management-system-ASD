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
| Department roster | `student1_department_<slug>` / `student1/departments/<slug>` | Names of all staff in the department (kept short so it ranks for "who is in X?") |
| Status roster | `student1_status_<slug>` / `student1/status/<slug>` | Names of all staff with that employment status (Active, On Leave, ...) |
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

Student 4 contributes research and grant context through `load_student4_context()`, which reads
from `STUDENT4_BACKEND_URL` (`/projects`, `/projects/<id>/grants`, `/projects/<id>/publications`)
rather than the database directly, and resolves lead/publication staff names via
`STUDENT1_BACKEND_URL`'s `/api/staff/<id>` (degrading to `staff ID <id> (name unavailable)` if
that service is unreachable). Emits one `tier_1` chunk per project, grant and publication, plus a
summary-counts chunk, all tagged `feature="research_grant_management"`, `student=4`.

## Student 5 - Performance & Professional Development

Student 5 contributes performance and professional-development context through `load_student5_context()`.

- Source: Student 5 backend/API (`STUDENT5_BACKEND_URL`, default `http://localhost:5005`). The loader reads `GET /api/performance-reviews`, `/api/development-goals`, `/api/training-programs`, `/api/staff-training`, and `/api/development-recommendations`. It optionally reads `GET /api/integration/staff` for display names. It never opens the feature database directly.
- Every chunk uses `feature="performance_professional_development"`, `student=5`, and `authority_tier="tier_1"`.

| Chunk | `chunk_id` / `source_id` | Content |
|---|---|---|
| Performance review | `student5_reviews_<id>` / `student5/performance-reviews/<id>` | Review date, reviewer ID, rating, feedback and status for one staff member |
| Development goal | `student5_goals_<id>` / `student5/development-goals/<id>` | Title, description, target date, progress and status |
| Training program | `student5_programs_<id>` / `student5/training-programs/<id>` | Title, skill area, provider, dates and description |
| Staff training | `student5_training_<id>` / `student5/staff-training/<id>` | Staff member, linked program title, enrolment and completion dates, and participation status |
| Recommendation | `student5_recommendations_<id>` / `student5/development-recommendations/<id>` | Proposed action, rationale, related goal, generation date and decision status |
| Totals | `student5_summary_counts` / `student5/summary` | Counts for staff and each of the five record types |

Staff IDs remain usable when the staff directory is unavailable. Recommendations are labelled as proposals; a `Pending` or `Accepted` decision does not prove the action was completed. If a required Student 5 API cannot be read, this loader returns no Student 5 chunks so the shared refresh can still index other features.
