# Performance and Professional Development Management

Matthew Barnard's Release 0 feature manages staff reviews, development goals, training programs, training enrolments, and development recommendations.

## What is implemented

- A responsive frontend dashboard at `http://localhost:8005`.
- Full create, read, update, delete, and filtering support for all five resources.
- A Flask backend API at `http://localhost:5005`.
- A separate Flask/SQLite database service at `http://localhost:5105`.
- Relational constraints, validation, and ten seed records per table.
- Visible AI Mode that uses a local Ollama model to produce a grounded development recommendation and saves it as `Pending` for human review.
- Three feature containers coordinated by Docker Compose, plus the team's shared Ollama runtime.
- The team stylesheet and navigation back to the unified homepage.
- Automated database, API, and mocked AI-route tests.
- A GitHub Actions workflow that runs tests and validates/builds the containers.

AI Mode makes a recommendation request and may make one correction request when the local model breaks a database constraint. This small output-validation step is not being represented as the team's shared Plan -> Act -> Observe -> Adapt software-development loop; that integration and its genuine execution logs must be added with the group later.

## Architecture

```text
Browser :8005
    |
    v
Nginx frontend -- /api --> Flask backend :5005 --> database service :5105 --> SQLite
                                  |
                                  +--> shared Ollama service :11434
```

Only the database service reads or writes SQLite. The backend performs orchestration and exposes the public API. Nginx serves the browser files and proxies `/api` requests, avoiding hard-coded browser-side service addresses.

In the integrated stack, the backend also reads the Staff Management directory through `STAFF_SERVICE_URL`. The frontend displays matching staff names, and AI Mode can include the staff member's profile and expertise in its grounded context. Both fall back to Matthew's numeric IDs and records if Staff Management is not running.

## Run the integrated group application

From the repository root:

```powershell
docker compose up --build -d
docker compose exec ollama ollama pull qwen2.5:0.5b
```

Open `http://localhost:8000` for the shared homepage or `http://localhost:8005` for this feature directly. The shared Compose file supplies the common stylesheet and connects the backend to the shared Ollama container.

## Run this feature by itself

From this directory:

```powershell
docker compose up --build
docker compose exec ollama ollama pull qwen2.5:0.5b
```

Open `http://localhost:8005`. Stop the application with:

```powershell
docker compose down
```

SQLite data is retained in the named `matthew-performance-data` volume across ordinary container restarts.

## AI Mode

Both Compose configurations connect the backend to an Ollama container at `http://ollama:11434/v1`. Pull the model into the corresponding Compose stack once with `docker compose exec ollama ollama pull qwen2.5:0.5b`. The normal CRUD feature continues to work if the model is unavailable; the AI panel reports that service separately.

AI output is parsed and checked against database context before it is saved. If both model attempts break a database constraint, the service returns a clearly labelled fallback selected only from the staff member's recorded goal and the training catalogue. A generated record remains `Pending` until a person accepts, rejects, or edits it.

## API resources

Each resource supports `GET` collection, `GET` by ID, `POST`, `PUT`, and `DELETE` through `/api/<resource>`:

- `performance-reviews`
- `development-goals`
- `training-programs`
- `staff-training`
- `development-recommendations`

Examples:

```text
GET  /api/development-goals?staffID=1&status=In%20Progress
POST /api/performance-reviews
PUT  /api/development-recommendations/1
DELETE /api/staff-training/12
```

Health endpoints are `/health`, `/api/health`, and `/api/ai/health` on the backend, and `/health` on the database service.

## Run tests without Docker

Install both requirement sets, then run each suite in its own service directory:

```powershell
python -m pip install -r backend-service/requirements.txt
python -m pip install -r database-service/requirements.txt

Set-Location database-service
python -m unittest discover -s tests -v
Set-Location ../backend-service
python -m unittest discover -s tests -v
```

The backend AI endpoint is mocked in automated tests, so CI does not need to download or run an LLM. A real local Ollama request is demonstrated separately through the UI.

## Release 0 evidence

See `../docs/release-0/student-5-evidence-guide.md` for what to capture now, what belongs to the later shared agentic-loop work, and a showcase recording checklist.
