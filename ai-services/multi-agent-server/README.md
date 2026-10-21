# Multi-Agent Server (Release 2)

One shared, non-containerised server that runs a **Planner → Worker → Reviewer → Human Review** workflow for any of the five features. It runs on the host next to Ollama, the MCP server (5201) and the RAG server (5200), on port **5202**.

```text
Frontend tab → feature backend → Multi-Agent Server (5202)
                                   1. Planner Agent    plan: Objective / Steps / Evidence Required / Human Approval
                                   2. Worker Agent     evidence from that feature's backend API → Output / Evidence Used / Limitations
                                   3. Automated checks sections present, sources cited, every cited source was supplied
                                   4. Reviewer Agent   Risk / Correction / Retest / Recommendation
                                   5. Human Review     Accept | Partially Accept | Correct | Reject
```

Every run is written to `workflow_history.jsonl` (the workflow and its human decision) and `coordination_audit.jsonl` (one line per step with status and timing). Both are git-ignored runtime files; copy them into `reports/` for evidence.

## Run

Ollama needs `qwen2.5:0.5b` and `llama3.1:8b` (`ollama pull <model>`).

```bash
cd ai-services/multi-agent-server
pip install -r requirements.txt
python app.py                      # http://localhost:5202
```

The feature backends you want evidence from must be running (Docker Compose or locally).

### From the terminal

```bash
python workflow_runner.py run --feature student3 "Which staff members are overloaded?"   # asks for the human decision at the end
python workflow_runner.py run --no-review --feature student3 "..."                         # decide later
python workflow_runner.py decide <workflow_id> --decision Accept --reviewer "Your Name"
python workflow_runner.py status
python workflow_runner.py history --feature student3
```

### Tests and scans

```bash
python -m unittest discover -s tests          # 17 tests, no Ollama or backends needed
ruff check --select S .                        # security rules
pip-audit -r requirements.txt
```

## API

| Method | Path | Body / query | Returns |
|---|---|---|---|
| GET | `/health` | | service, models, features, decision values |
| GET | `/features` | | registered features and their evidence |
| POST | `/workflow` | `{"user_request": "...", "feature": "student3"}` | full workflow, `status: awaiting_human_review` |
| POST | `/workflow/<id>/decision` | `{"decision": "Accept", "reviewer": "...", "notes": "...", "correction": "..."}` | workflow with the decision merged in |
| GET | `/workflow/<id>` | | one workflow (with decision, if any) |
| GET | `/workflow/history` | `?feature=student3&limit=20` | recent workflows, newest first |
| GET | `/workflow/status` | | counts (runs, decisions, pending, audit records) and the latest workflow |

- `feature` accepts `student1`–`student5` (or `3`, `Student 3`).
- `decision` is one of `Accept`, `Partially Accept`, `Correct`, `Reject`. `Correct` requires `correction`. Each workflow can be decided once (a second decision returns 409).
- Bad input returns 400; an unknown workflow id returns 404.

```bash
curl -X POST localhost:5202/workflow -H "Content-Type: application/json" \
  -d '{"user_request": "Which staff members are overloaded?", "feature": "student3"}'
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MULTI_AGENT_PORT` / `MULTI_AGENT_HOST` | `5202` / `0.0.0.0` | listen address (all interfaces so Docker backends can reach it) |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` | Ollama OpenAI-compatible endpoint |
| `OLLAMA_PLANNER_MODEL` | `qwen2.5:0.5b` | Planner |
| `OLLAMA_WORKER_MODEL` | `llama3.1:8b` | Worker (qwen2.5:0.5b echoed evidence or mislabelled records) |
| `OLLAMA_REVIEW_MODEL` | `llama3.1:8b` | Reviewer |
| `OLLAMA_TIMEOUT_SECONDS` / `OLLAMA_REVIEW_TIMEOUT_SECONDS` | `90` / `180` | per-call model timeouts |
| `STUDENT1_BACKEND_URL` … `STUDENT5_BACKEND_URL` | `http://127.0.0.1:5001` … `5005` | where evidence is read from |
| `MAX_EVIDENCE_ITEMS` | `20` | evidence items passed to the Worker (most relevant to the request first) |

Defaults use `127.0.0.1` rather than `localhost`: on Windows, `localhost` tries IPv6 first and adds about 2 seconds to every request to an IPv4-only Flask server.

If Ollama is down the workflow still completes with fallback text, a reviewer recommendation not to accept, and the human decision still required. If a feature backend is down, the Worker returns `no_evidence` without calling a model.

## Adding your feature (each student)

**1. Evidence (this server).** Your section in `evidence.py` is marked `OWNER: Student N` and is a placeholder until you fill it in; until then a workflow for your feature returns `no_evidence` with "Student N evidence is not implemented yet". Read data through a route your backend already exposes (the ones your RAG loader or MCP tools use are a good start) and return a list of evidence items, e.g. `items_from(rows, "student1/staff")`. Each item's `source` (e.g. `student3/profiles/1`) is what the Worker cites. Contact fields (`email`, `phone`, ...) are dropped automatically. Then replace the `TODO` in your `evidence_description` in `FEATURES`, since the Planner reads it. Student 3's section is a complete example.

**2. Backend route (your backend).** Proxy to the server, switchable off like MCP and RAG:

```python
MULTI_AGENT_SERVER_URL = os.environ.get("MULTI_AGENT_SERVER_URL", "http://host.docker.internal:5202")

def _multi_agent_enabled():
    return os.environ.get("MULTI_AGENT_ENABLED", "false").lower() == "true"

@multi_agent_bp.post("/multi-agent/workflow")
def run():
    if not _multi_agent_enabled():
        return jsonify({"error": "Multi-Agent mode is off."}), 403
    body = request.get_json(silent=True) or {}
    resp = requests.post(f"{MULTI_AGENT_SERVER_URL}/workflow",
                         json={"user_request": body.get("user_request", ""), "feature": "student3"},
                         timeout=300)
    return jsonify(resp.json()), resp.status_code

# Also forward POST /multi-agent/workflow/<id>/decision and GET /multi-agent/workflow/history the same way.
```

Always send your own feature key so the Worker only sees your evidence.

**3. Frontend tab.** A request box, Run Workflow, the Planner / Worker / Reviewer output and automated checks, Accept / Partially Accept / Correct / Reject buttons with a reviewer name, notes and correction field, and a history list.

**4. Configuration.** In `docker-compose.yml` add `MULTI_AGENT_ENABLED: "true"` and `MULTI_AGENT_SERVER_URL: http://host.docker.internal:5202` to your backend. In your `student-x.yml` CI run set `MULTI_AGENT_ENABLED=false` and check the route returns 403, like MCP and RAG. The cloud deployment keeps it off by default.
