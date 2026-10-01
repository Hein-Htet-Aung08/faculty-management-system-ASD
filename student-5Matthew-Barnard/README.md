# Performance and Professional Development Management

This is Matthew Barnard's feature for managing staff performance and
professional development. It includes performance reviews, development goals,
training programs, staff enrolments, and development recommendations.

## Features

- Create, view, update, delete, and filter records from the frontend
- Ten example records in each database table
- Validation and relationships between related records
- AI-assisted training recommendations using the shared Ollama service
- Staff names and details loaded from the Staff Management service
- Automated tests for the database, API, and AI route
- A GitHub Actions workflow that runs the tests and checks the Docker builds
- Separate frontend, backend, and database containers

The main dashboard is available at `http://localhost:8005`. The backend API
runs on port `5005`, and the database service runs on port `5105`.

## Architecture

```text
Browser :8005
    |
    v
Nginx frontend -- /api --> Flask backend :5005 --> Database service :5105 --> SQLite
                                  |
                                  +--> Shared Ollama service :11434
                                  +--> Shared local MCP server :5201
                                  +--> Shared local RAG server :5200
```

The frontend is served by Nginx, which also sends `/api` requests to the
backend. The backend handles the feature logic and communicates with the
database, Ollama, MCP and RAG services. Only the database service directly
accesses the SQLite database.

When the full group application is running, the backend also gets staff names
and details from the Staff Management service. If that service is unavailable,
the feature can still display and manage records using their staff IDs.

## Running the Full Application

From the repository root, run:

```powershell
docker compose up --build -d
docker compose exec ollama ollama pull qwen2.5:0.5b
```

Open `http://localhost:8000` for the group homepage, or
`http://localhost:8005` to open this feature directly.

To stop the application, run:

```powershell
docker compose down
```

## Running This Feature by Itself

From the `student-5Matthew-Barnard` folder, run:

```powershell
docker compose up --build
docker compose exec ollama ollama pull qwen2.5:0.5b
```

Open `http://localhost:8005`. To stop the containers, run:

```powershell
docker compose down
```

The SQLite data is stored in the `matthew-performance-data` Docker volume, so
it remains available after the containers are restarted.

## AI Mode

AI Mode uses `qwen2.5:0.5b` through the shared Ollama container. It combines a
staff member's details, current goal, and the available training programs to
suggest a suitable development activity.

The backend checks the response before saving it. If the response contains
invalid database values, it asks the model to correct them once. If the second
response is also invalid, it creates a basic recommendation from existing
database records instead. New recommendations are saved as `Pending` so they
can be reviewed, edited, accepted, or rejected by a user.

The normal management pages continue to work when Ollama is unavailable. Only
the AI recommendation request will show an error.

## MCP Tools

The MCP Tools tab uses two read-only tools on the shared local MCP server.
Staff development summary shows a staff member's reviews, goals, training and
recommendations. Training by skill area finds catalogue programs using a
case-insensitive match. Both requests travel from the frontend through this
feature's backend to the shared server. The server reads the existing Student 5
backend APIs; it does not access the SQLite database directly.

Start the shared MCP server on the host after installing its requirements:

```powershell
python -m pip install -r ai-services/mcp-server/requirements.txt
Set-Location ai-services/mcp-server
python server.py
```

Run these commands from the repository root before opening another terminal to
start the integrated Docker Compose application. The MCP server listens at
`http://localhost:5201/mcp`. The integrated Compose configuration enables MCP
for Student 5 and connects its backend to the host through
`host.docker.internal`. When running the backend directly on the host, set
`MCP_ENABLED=true` and `MCP_SERVER_URL=http://localhost:5201/mcp`.

To validate through the UI, open `http://localhost:8005`, choose MCP Tools,
request the summary for staff ID 1, and search for skill area `Leadership`.
Both should return recorded data, including the Academic Leadership Foundations
training title. The backend also exposes `POST /api/mcp/development-summary`
with `{"staffID":1}` and `POST /api/mcp/training-by-skill` with
`{"skillArea":"Leadership"}`. `GET /api/mcp/status` reports whether MCP is
enabled. MCP defaults to disabled outside the Compose deployment and is
explicitly disabled in CI.

## RAG Context

The shared local RAG server reads this feature's five list APIs and adds one
source chunk for each performance review, development goal, training program,
staff training record, and development recommendation. It also adds a totals
chunk. The server uses `/api/integration/staff` for names when available and
keeps staff IDs when the staff service is offline. The RAG loader only reads
backend APIs; it does not open this feature's SQLite database.

Start this feature's backend and database before refreshing the shared RAG
corpus. From the repository root, install the RAG requirements, then run:

```powershell
python -m pip install -r ai-services/rag-server/requirements.txt
Set-Location ai-services/rag-server
python rag_http_server.py
```

`STUDENT5_BACKEND_URL` defaults to `http://localhost:5005` and can be set to a
different backend address. The loader skips Student 5 context when a required
feature API is unavailable; refresh the corpus again after the backend starts.
The six Student 5 retrieval questions are in `ai-services/rag-server/rag_eval.py`.

The RAG Questions tab sends requests through `POST /api/rag/ask` on this
feature's backend. The backend calls the shared local RAG service and returns
the grounded answer, citations and confidence category. The tab also has a
Refresh context button, which calls `POST /api/rag/refresh` after records
change. The shared HTTP server listens at `http://localhost:5200`; the
integrated Compose deployment connects the backend through
`host.docker.internal`. For a backend running directly on the host, set
`RAG_ENABLED=true` and `RAG_SERVER_URL=http://localhost:5200`.

To demonstrate the feature, start the Student 5 backend and database and the
shared RAG HTTP server, refresh context in the tab, then ask about the
"Strengthen academic leadership" goal. The answer should show source IDs and
a confidence category. Ask an unrelated question to check the
insufficient-context message. RAG defaults to disabled outside Compose and is
disabled in CI.

## API Endpoints

Each resource supports `GET`, `POST`, `PUT`, and `DELETE` requests through
`/api/<resource>`:

- `performance-reviews`
- `development-goals`
- `training-programs`
- `staff-training`
- `development-recommendations`

Example requests:

```text
GET    /api/development-goals?staffID=1&status=In%20Progress
POST   /api/performance-reviews
PUT    /api/development-recommendations/1
DELETE /api/staff-training/12
```

The backend health endpoints are `/health`, `/api/health`, and
`/api/ai/health`. The database service also has a `/health` endpoint.

## Running the Tests

The tests can be run without Docker. Install the requirements first:

```powershell
python -m pip install -r backend-service/requirements.txt
python -m pip install -r database-service/requirements.txt
```

Then run the database and backend test suites:

```powershell
Set-Location database-service
python -m unittest discover -s tests -v
Set-Location ../backend-service
python -m unittest discover -s tests -v
```

The automated tests use a mocked Ollama response, so the AI model does not
need to be downloaded in GitHub Actions.

## Release 0 Evidence

The Release 0 evidence checklist is in
[`../docs/release-0/student-5-evidence-guide.md`](../docs/release-0/student-5-evidence-guide.md).
