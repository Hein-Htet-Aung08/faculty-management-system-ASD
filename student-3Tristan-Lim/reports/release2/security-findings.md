# Student 3 – Pre-Commit Security Findings (Release 2)

Scans: Ruff security rules (`--select S`), detect-secrets, pip-audit, configured in
`student-3Tristan-Lim/.pre-commit-config.yaml` and run on every commit. They cover the
Student 3 feature (backend, database, tests) and the shared Multi-Agent Server
(`ai-services/multi-agent-server`), which Student 3 owns.
Final result: all three passed (`precommit-results.txt`).

## Findings from the first scan and how they were handled

| Tool | Finding | Location | Action |
|---|---|---|---|
| Ruff S201 | Flask `debug=True` – the Werkzeug debugger allows code execution from the browser, and both Docker images run `python app.py` | `backend-service/app.py`, `database-service/app.py` | **Fixed.** Debug is now opt-in via `FLASK_DEBUG=true` and off by default |
| Ruff S104 | Server binds to `0.0.0.0` | `backend-service/app.py`, `database-service/app.py`, `multi-agent-server/app.py` | **Accepted.** Required so each service is reachable from outside its container (and, for the Multi-Agent Server, from Docker backends via `host.docker.internal`); host comes from `HOST` / `MULTI_AGENT_HOST`, marked `# noqa: S104` with the reason |
| Ruff S608 | SQL built with f-strings (8 in the database API, 1 in seeding) | `database-service/app.py`, `database-service/init_db.py` | **Accepted, false positive.** Only identifiers from `schema.TABLES` are interpolated: the table name is checked against that allowlist, the primary key comes from the schema and column names are filtered against the schema's columns. Every value is bound as a `?` parameter. Documented in the code and marked `# noqa: S608` per line |
| Ruff S314 | `xml.etree` parsing | `tests/summarise_results.py` | **Accepted.** Parses only the JUnit file pytest writes earlier in the same CI job, never outside input; marked `# noqa: S314` |
| Ruff S101 | `assert` statements | `tests/` | **Excluded for tests only** (`ruff.toml`). `assert` is how pytest checks results; still enforced in backend and database code |
| detect-secrets | Secret Keyword: `api_key="ollama"` | `multi-agent-server/agents/llm_client.py` | **Accepted, false positive.** Ollama ignores the key but the OpenAI client requires one; marked `# pragma: allowlist secret` with the reason |
| pip-audit | `flask 3.0.3` – PYSEC-2026-2151 | backend, database and Multi-Agent Server requirements | **Fixed.** Upgraded to `flask==3.1.3` |
| pip-audit | `flask-cors 4.0.1` – PYSEC-2024-71, PYSEC-2026-1383/1384/1385 | `backend-service/requirements.txt` | **Fixed.** Upgraded to `flask-cors==6.0.0`; CORS preflight from the frontend origin still succeeds |
| pip-audit | `requests 2.32.3` – PYSEC-2026-1872, PYSEC-2026-2275 | `backend-service/requirements.txt` | **Fixed.** Upgraded to `requests==2.33.0` |

## Verification after the fixes

- All Student 3 tests pass (14 passed, 4 live tests skipped locally; the live tests run in CI against the containers), on Python 3.11 with the upgraded packages.
- The dashboard, CRUD, MCP tools and a full Multi-Agent workflow were re-tested in the browser with the upgraded packages; both Flask services log `Debug mode: off`.
- All 17 Multi-Agent Server tests pass.
- `student-3-TristanLim.yml` passed on GitHub Actions after each change.
