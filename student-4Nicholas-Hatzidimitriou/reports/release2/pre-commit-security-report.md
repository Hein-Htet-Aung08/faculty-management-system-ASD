# Student 4 Pre-Commit Security Testing Report

Date: 2026-10-21
Student: Nicholas Hatzidimitriou (Student 4, Research & Grant Management)
Scope: `student-4Nicholas-Hatzidimitriou/**` (my own code) plus the shared `ai-services/*`
files I maintain (`ai-services/mcp-server/`, `ai-services/rag-server/`,
`ai-services/agentic_loop/collectors/db_collector.py`,
`ai-services/agentic_loop/collectors/development_integrity_collector.py`). Findings in the
other four students' folders are reported for visibility but **not fixed here** — each
student is responsible for their own code, per the Release 2 brief's ownership model.

## Tooling introduced (shared config, new)

- `pyproject.toml` — `[tool.ruff.lint] select = ["S"]` (flake8-bandit security rules only),
  with `"**/tests/**" = ["S101"]` to allow `assert` in any student's test folder.
- `.pre-commit-config.yaml` — three local hooks: `ruff-scan`, `detect-secrets-scan`,
  `pip-audit-scan`.
- `scripts/pre_commit_pytest.py` — cross-platform launcher (`cd` to repo root, run pytest),
  avoids hardcoding `.venv/bin/python` vs `.venv/Scripts/python.exe`.
- `tests/pre_commit/test_ruff_scan.py`, `test_secrets_scan.py`, `test_dependency_audit.py`.
- `.secrets.baseline` — one confirmed false positive baselined (see below).
- A project venv (`.venv/`) with `pytest`, `ruff`, `detect-secrets`, `pip-audit`, `pre-commit`
  installed, per the lab's explicit instruction to install into the project venv rather than
  system Python.

## Commands run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest requests pre-commit ruff detect-secrets pip-audit
.venv/bin/pre-commit install
.venv/bin/pre-commit run --all-files
```

## Ruff scan (flake8-bandit security rules)

First run across the whole repo: **138 findings**. 95 of these were `S101` (`assert` in test
files) caused by a bug in my first draft of the `per-file-ignores` glob (`"tests/**"` only
matches a top-level `tests/` folder, not the nested `backend/tests/`, `tests/lab_x/`, etc. that
every student actually uses). Fixed the glob to `"**/tests/**"`, which eliminated all 95 — they
were never real findings, just a missing exclude pattern.

Remaining real findings in **my own code**, all fixed:

| File | Finding | Fix |
|---|---|---|
| `student-4Nicholas-Hatzidimitriou/backend/app.py:36` | S104 (bind `0.0.0.0`) + S201 (`debug=True`) | `debug` now reads `FLASK_DEBUG` env var (default `false`); `noqa: S104` with reason - container needs to bind all interfaces |
| `student-4Nicholas-Hatzidimitriou/database-service/app.py:614` | Same | Same fix |
| `student-4Nicholas-Hatzidimitriou/frontend/app.py:37` | Same | Same fix |

Findings in **shared `ai-services/` code I maintain**, all fixed:

| File | Finding | Fix |
|---|---|---|
| `ai-services/mcp-server/server.py:12` | S104 (bind `0.0.0.0`) | `noqa: S104` - this host process must bind all interfaces so containerised backends can reach it via `host.docker.internal` |
| `ai-services/rag-server/rag_http_server.py:310` | Same | Same fix |
| `ai-services/rag-server/rag_pipeline.py:2357` | S110 (`except: pass`) | Replaced with `logger.warning(...)` - a real fix, not a suppression. Added `import logging` + module-level `logger` |
| `ai-services/agentic_loop/collectors/db_collector.py:35` | S608 (possible SQL injection) | `noqa: S608` - the table name comes from `sqlite_master` (the database's own schema), not external input; confirmed by reading the line above where it's queried |
| `ai-services/agentic_loop/collectors/development_integrity_collector.py:47` | S608 | `noqa: S608` - table/columns come from the module's own fixed `RESOURCES` config dict, not external input |
| `ai-services/agentic_loop/collectors/development_integrity_collector.py:90, 93` | S310 (`urlopen` scheme) | `noqa: S310` - `base_url` is `os.getenv("STUDENT5_DB_URL", "http://localhost:5105")`, a fixed internal service URL, not external input |

**Before/after, `student-4Nicholas-Hatzidimitriou/backend/app.py`:**
```python
# Before
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=True)

# After
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=debug_mode)  # noqa: S104 - container needs to bind all interfaces
```

Remaining findings after my fixes, **in other students' own folders, not touched**:

```
student-1-Andy-Lam/backend/app.py:407         S104, S201
student-1-Andy-Lam/tests/conftest.py:38       S603
student-2Hein-Htet-Aung/backend/app.py:80     S104
student-2Hein-Htet-Aung/database/app.py:579   S104, S201
student-3Tristan-Lim/backend-service/app.py:37    S104
student-3Tristan-Lim/database-service/app.py (×8 lines)  S608
student-3Tristan-Lim/database-service/app.py:184  S104, S201
student-3Tristan-Lim/database-service/init_db.py:164  S608
student-5Matthew-Barnard/backend-service/app.py:246   S104
student-5Matthew-Barnard/database-service/app.py (×8 lines)  S608
student-5Matthew-Barnard/database-service/app.py:183  S104
student-5Matthew-Barnard/database-service/database.py (×2 lines)  S608
```

**31 findings remain, all in students 1/2/3/5's own code.** `pre-commit run --all-files` will
not pass repo-wide until each of them fixes or documents their own findings - this is expected
under the brief's ownership model ("each student runs and reports on their own code"), not a
bug in this report.

## detect-secrets scan

One finding: `student-2Hein-Htet-Aung/backend/services/llm_client.py:29`, where an `api_key`
keyword argument is set to the literal word used as a placeholder for local Ollama servers.
Confirmed false positive - this is the required placeholder value for an OpenAI-compatible
client pointed at a local Ollama server, not a credential. Baselined in `.secrets.baseline`
with `"is_secret": false` (an audited false positive, not a silent suppression - the finding
is still visible in the baseline file for anyone to review). No real secrets found anywhere
else in the repo.

## pip-audit scan

Adapted per the brief: one venv can't represent 15 services, so `test_dependency_audit.py`
runs `pip-audit -r <file>` against every `requirements.txt` in the repo individually (found via
`rglob`), not just the active venv.

**Fixed in my own three `requirements.txt` files:**

| Package | Before | After | CVEs fixed |
|---|---|---|---|
| Flask | 3.0.3 | 3.1.3 | PYSEC-2026-2151 |
| flask-cors | 4.0.1 | 6.0.0 | PYSEC-2024-71, PYSEC-2026-1383/1384/1385 |
| requests | 2.32.3 | 2.33.0 | PYSEC-2026-1872, PYSEC-2026-2275 |
| python-dotenv | 1.0.1 | 1.2.2 | PYSEC-2026-2270 |

Applied to `student-4Nicholas-Hatzidimitriou/{backend,database-service,frontend}/requirements.txt`.
`pip-audit -r <file>` now reports "No known vulnerabilities found" for all three.

**This was a real upgrade, not just an edit** - `flask-cors` 4→6 is a major version bump, so I
rebuilt all three Docker images and ran them against the real database container before
trusting the change:
- `backend`: `/health` → 200, `/projects` → 200, and a real CORS preflight request
  (`OPTIONS /projects` with an `Origin` header) still returns the expected
  `Access-Control-Allow-Origin`/`Access-Control-Allow-Methods` headers.
- `database-service`: `/projects` → 200.
- `frontend`: `/` → 200.

All three images and containers were removed after the test.

**Not fixed - no fix available upstream:** `ai-services/rag-server/requirements.txt` pins
`chromadb` (unpinned, resolves to 1.5.9, the current latest release). `pip-audit` flags 4 CVEs
against it (PYSEC-2026-311, -3813, -3814, -3815), none of which list a fix version. I checked
PyPI directly - 1.5.9 is the newest release, so there is no newer version to upgrade to yet.
Documenting this openly rather than suppressing it: this is a known, currently-unfixable
dependency risk in the shared RAG server, to be revisited once chromadb ships a patched
release.

**Found in other students' files, not fixed (their own responsibility):** the same
Flask/flask-cors/requests vulnerabilities appear in students 1, 2, 3 and 5's `requirements.txt`
files, at the same pinned versions. Same upgrade path (`Flask==3.1.3`, `flask-cors==6.0.0`,
`requests==2.33.0`) would resolve theirs too.

## Blocked-commit verification

Planted a fake secret (an `AWS_SECRET_ACCESS_KEY` variable assigned a string matching AWS's
well-known access-key-ID pattern, deliberately not reproduced literally here so this report
itself doesn't trip the same scanner) in a throwaway file, staged it, and attempted a real
commit:

```bash
git add student-4Nicholas-Hatzidimitriou/fake_secret_test.py
git commit -m "test: deliberately planted fake secret to verify pre-commit blocks it"
```

Result: **blocked**. All three hooks ran; `detect-secrets-scan` failed specifically on the
planted key (confirmed by reading the hook's own test output, not just the overall exit code).
`git log` confirms no new commit was created - the most recent commit is still the prior merge
commit. The fake-secret file was then removed from the index and the working tree.

## Summary

- 3 real findings fixed in my own code (S104 + S201, ×3 files).
- 5 real/false-positive findings resolved in shared `ai-services/` code I maintain (2× S104
  real-but-intentional, 1× S110 real fix with logging, 2× S608 false positive, 2× S310 false
  positive).
- 1 confirmed false-positive secret baselined (not suppressed - visible and justified in
  `.secrets.baseline`).
- 4 real dependency vulnerabilities fixed across my own 3 `requirements.txt` files, verified by
  rebuilding and smoke-testing all three containers against the real database.
- 1 dependency vulnerability (chromadb) documented as currently unfixable upstream.
- 31 findings remain in other students' own folders - not fixed here, flagged for them.
- Commit-blocking behaviour verified with a real planted secret, then reverted.
