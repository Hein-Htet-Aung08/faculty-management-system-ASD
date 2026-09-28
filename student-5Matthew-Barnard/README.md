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
```

The frontend is served by Nginx, which also sends `/api` requests to the
backend. The backend handles the feature logic and communicates with the
database and Ollama services. Only the database service directly accesses the
SQLite database.

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
