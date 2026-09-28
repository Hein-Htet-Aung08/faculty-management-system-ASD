# Faculty Management System (ASD 2026)

An integrated, microservices-based Faculty Management System built as part
of the ASD 2026 semester project. Five students each own a full-stack
feature (frontend, backend/API, and database), integrated into a single
application and driven by a shared open-source LLM (Ollama) following the
project's **Plan → Act → Observe → Adapt** Agentic AI workflow.

## Team & Features

| Student | Feature | Folder |
|---|---|---|
| Andy Lam | Staff Management | `student-1-Andy-Lam/` |
| Hein Htet Aung | Teaching, Subject & Classroom Allocation | `student-2Hein-Htet-Aung/` |
| Tristan Lim | Workload & Availability Management | `student-3Tristan-Lim/` |
| Nicholas Hatzidimitriou | Research & Grant Management | `student-4Nicholas-Hatzidimitriou/` |
| Matthew Barnard | Performance & Professional Development | `student-5Matthew-Barnard/` |

## Tech Stack
- **Backend:** Python 3.11, Flask REST APIs
- **Frontend:** HTML/CSS/JavaScript (see Known Issues below regarding HTMX)
- **Database:** SQLite (per-feature, containerised)
- **AI:** Ollama (local LLM runtime) running `qwen2.5:0.5b`
- **Containerisation:** Docker & Docker Compose
- **CI/CD:** GitHub Actions (one independent workflow per student)

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Hein-Htet-Aung08/faculty-management-system-ASD.git
   cd faculty-management-system-ASD
   ```

2. **Build and start the full application**
   ```bash
   docker-compose up -d --build
   ```
   This builds and starts all five feature stacks, the shared Ollama
   runtime, and the unified home page. First run will take a few minutes
   while Docker images build and the LLM model is pulled.

3. **Open the application**
   Once everything is running, open:
   ```
   http://localhost:8000
   ```
   This is the unified home page, linking out to all five features below.

4. **Stop the application**
   ```bash
   docker-compose down
   ```

## Service Access Points

| Service | Frontend | Backend API |
|---|---|---|
| Unified home page | http://localhost:8000 | — |
| Staff Management | http://localhost:8001 | http://localhost:5001 |
| Teaching Subject & Classroom Allocation | http://localhost:8002 | http://localhost:5002 |
| Workload & Availability Management | http://localhost:8003 | http://localhost:5003 |
| Research & Grant Management | http://localhost:8004 | http://localhost:5004 |
| Performance & Professional Development | http://localhost:8005 | http://localhost:5005 |
| Ollama (shared AI runtime) | — | http://localhost:11434 |

## Repository Structure
See [`docs/architecture/`](docs/architecture/) for detailed architecture
diagrams, and the project's Repository Structure section in the technical
report for a full breakdown. At a high level:

```
faculty-management-system-ASD/
├── .github/workflows/     # One CI/CD workflow per student
├── ai-services/           # Shared AI-Mode / agentic review tooling
├── docs/                  # Architecture diagrams, reports, release evidence
├── shared/                # Unified home page + shared CSS theme
├── student-1-Andy-Lam/    
├── student-2Hein-Htet-Aung/
├── student-3Tristan-Lim/
├── student-4Nicholas-Hatzidimitriou/
├── student-5Matthew-Barnard/
└── docker-compose.yml     # Single shared configuration for the whole app
```

## Agentic AI Workflow
Each feature implements the shared **Plan → Act → Observe → Adapt** loop
when generating AI-assisted output (e.g. staff suitability analysis,
teaching staff recommendations), calling the shared Ollama runtime rather
than each maintaining a separate model instance.

## Running the Agentic Loop (AI Code Review Tool)
`ai-services/agentic_loop/` is a separate, standalone dev-tooling script —
it is **not** part of the running application and is not started by
Docker Compose. It uses AI agents to review each student's code (database
schema, backend endpoints, AI-Mode integration, and overall architecture)
against real, collected evidence from the repository.

1. **Make sure the shared Ollama container is running** (via
   `docker-compose up -d ollama`, or the full `docker-compose up -d
   --build` above) and reachable at `http://localhost:11434` from your
   host machine.

2. **Pull the required models** into the running Ollama container, if not
   already present:
   ```bash
   docker exec -it ollama ollama pull qwen2.5:0.5b
   docker exec -it ollama ollama pull llama3.1:8b
   ```

3. **Install the tool's Python dependencies** (a virtual environment is
   recommended):
   ```bash
   cd ai-services/agentic_loop
   pip install -r requirements.txt
   ```

4. **Run the tool:**
   ```bash
   python main.py
   ```
   You'll be shown a menu to choose a review mode:
   - `1` — DB: reviews each student's database schema/seed data
   - `2` — Endpoints: reviews each student's backend HTTP API
   - `3` — Architecture: reviews the overall team architecture and
     docker-compose wiring
   - `4` — AI-Mode: reviews each student's AI-Mode/Ollama integration
     (error handling, timeouts, prompt externalisation, output persistence)
   - `5` — Run All

5. **View the output.** Reports are written to
   `ai-services/agentic_loop/reports/` as both `.json` and `.md` files, one
   per student per mode (plus a single combined report for Architecture).

## Known Issues & Limitations
See the technical report's "Known Issues and Limitations" section for the
full list. Notable items:
- Frontend technology is inconsistent across features (HTMX vs. vanilla
  JavaScript) — see report for details.

## Project Documentation
Full technical reports, architecture diagrams, and release evidence for
Releases 0–2 are maintained in [`docs/`](docs/) and submitted separately
via Canvas per the ASD 2026 Project Specifications.
