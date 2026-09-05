# Team Agentic-Loop Codebase Reviewer

A shared, team-owned adaptation of the Lab 4 `agentic_loop/` pattern. Instead of
reviewing one app, it reviews the **five independent student microservices** in
this repo (`student-1-*` … `student-5-*`) plus the shared root
`docker-compose.yml`.

## The loop

Each mode runs the same deterministic stages, logged as `[MODE][STEP] message`:

```
START -> OBSERVE (collector) -> PROMPTS (registry) -> LLM -> [REVIEW] -> DONE
```

* **OBSERVE** – a collector gathers *real* evidence (SQLite queries, live HTTP
  requests, filesystem checks). No LLM runs here.
* **PROMPTS** – `PromptRegistry` loads the mode's prompt family from
  `prompts/<family>/…`. A missing file raises `FileNotFoundError` – it never
  silently continues with empty text.
* **LLM** – evidence is injected into `{{REVIEW_TARGET}}` / `{{VALIDATION_EVIDENCE}}`
  placeholders and sent to the implementation model (`OLLAMA_MODEL`).
* **REVIEW** – *architecture mode only*: a second, larger model
  (`OLLAMA_REVIEW_MODEL`) critiques the first model's output against the same
  evidence.
* If a collector returns `ok=False`, the loop short-circuits with
  `OBSERVE FAILED: …` and the model is never called.

## Modes

| # | Mode | Collector does | Prompt family | Review stage |
|---|------|----------------|---------------|--------------|
| 1 | DB | For each student: find `database-service/` or `database/`, probe its `/health` if it has an `app.py`, and inspect every `*.db` file directly – list tables, count rows, check the ≥10-records rule. | `service` | no |
| 2 | Endpoints | For each student: resolve `STUDENT<n>_BASE_URL`, regex-scan `routes/` for Flask decorators, then fire real `GET`/`POST` requests and record status + latency. Down services report `[CONNECTION REFUSED - app not running]`. | `service` | no |
| 3 | Architecture | For each student: confirm frontend entrypoint + backend `app.py` + database folder. For the shared stack: `docker-compose.yml` exists, defines `ollama`, and has an entry per student folder. | `team` | yes (2-model) |

## Layout

```
ai-services/
├── agentic_loop.py          # thin entrypoint (fixes sys.path, calls main())
└── agentic_loop/
    ├── main.py              # interactive menu
    ├── config/review_config.py
    ├── core/                # orchestrator, prompt_registry, ai_runner, reporter
    ├── collectors/          # db / endpoints / architecture  (+ common.py helpers)
    ├── pipelines/           # prompt assembly per mode
    └── prompts/service/…, prompts/team/…
```

## Run

```bash
pip install -r ai-services/agentic_loop/requirements.txt
cp ai-services/agentic_loop/.env.example ai-services/agentic_loop/.env   # then edit
python ai-services/agentic_loop.py
```

Menu: `1` DB · `2` Endpoints · `3` Architecture · `4` Run All · `0` Exit.

The collectors work with no LLM configured and no services running – they just
report what they find. The LLM is only needed for the review text at the end.

## Environment

| Var | Purpose | Default |
|-----|---------|---------|
| `OLLAMA_BASE_URL` | OpenAI-compatible endpoint | `http://localhost:11434/v1` |
| `OLLAMA_MODEL` | implementation model (quick checks) | `qwen2.5:0.5b` |
| `OLLAMA_REVIEW_MODEL` | architecture review model (deeper critique) | `llama3.1:8b` |
| `STUDENT<n>_BASE_URL` | student *n* backend | `http://localhost:500<n>` |
| `STUDENT<n>_DB_URL` | student *n* database-service (optional) | `http://localhost:510<n>` |
