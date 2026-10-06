# Student 5 RAG frontend and CI evidence

The RAG Questions tab sends a question to the Student 5 backend at
`POST /api/rag/ask`. The backend calls the shared local RAG HTTP server at
`/answer` and returns its answer, citations and confidence category. The tab
shows an insufficient-context message when the answer cannot be grounded.
Refresh context calls the backend at `POST /api/rag/refresh`, which calls the
shared `/refresh` endpoint. The browser does not contact the local RAG server
directly.

The root and Student 5 Compose files enable RAG for the Student 5 backend and
point it to `host.docker.internal:5200`. The RAG service itself remains outside
Compose. The Student 5 GitHub Actions workflow builds the frontend, backend
and database images and starts an isolated smoke-test stack with AI-Mode, MCP
and RAG explicitly disabled. It checks the disabled API behaviour and runs
the Student 5 RAG context tests.

Local validation on 1 October 2026:

- All 28 backend tests, 12 database tests, six MCP tests and four RAG context
  tests passed.
- Frontend JavaScript passed `node --check`.
- Both Compose files parsed and exposed the expected Student 5 RAG URL and
  enabled setting.
- A live HTTP check sent requests from the Student 5 backend to the shared RAG
  HTTP handler for `/answer` and `/refresh`. The handler returned a sample
  cited answer and a sample refresh count; the backend preserved both.

Docker Desktop was not running locally, so the container smoke-test job and
browser UI could not be executed here. The live HTTP check used a controlled
sample RAG response; the separate Student 5 context check used real seeded
backend records and Chroma retrieval. A successful GitHub Actions run and
integrated browser demonstration still need to be captured for the report.
